import glm
import numpy as np
import base64
import os
from pygltflib import GLTF2
from PIL import Image
import io


class InstancedModel3D:
    """
    Versión instanciada de Model3D.
    - Carga un GLB (POS + UV + INDICES + 1 textura baseColor)
    - Dibuja N instancias en una sola draw call (instancing)
    - Cada instancia tiene su propia matriz modelo (pos + rot + scale)
    """

    def __init__(self, app, model_path, instances):
        """
        instances: lista de dicts tipo:
            {
                "pos":   (x, y, z),
                "rot":   (rx, ry, rz),    # en grados
                "scale": 1.0  ó (sx,sy,sz)
            }
        """
        self.app = app
        self.ctx = app.ctx

        self.model_path = model_path
        self.model_dir = os.path.dirname(model_path)

        # Datos GLTF
        self.gltf = None
        self.buffer_data = []

        # Geometría
        self.vertices = None
        self.uvs = None
        self.indices = None

        # Instancias
        self.instances = instances
        self.instance_matrices = None
        self.instance_count = 0

        # Recursos GPU
        self.vbo = None
        self.ibo = None
        self.instance_vbo = None
        self.vao = None
        self.texture = None
        self.shader = None

        # Pipeline
        self._load_gltf()
        self._extract_mesh_data()
        self._load_textures()
        self._create_instance_matrices()
        self._create_shader()
        self._create_buffers()

    # -------------------------------------------------------------
    # CARGA GLB
    # -------------------------------------------------------------
    def _load_gltf(self):
        print(f"🔍 [Instanced] Cargando GLB: {self.model_path}")
        self.gltf = GLTF2().load(self.model_path)

        for b in self.gltf.buffers:
            if b.uri and b.uri.startswith("data:"):
                encoded = b.uri.split(",", 1)[1]
                self.buffer_data.append(base64.b64decode(encoded))
            elif b.uri:
                with open(os.path.join(self.model_dir, b.uri), "rb") as f:
                    self.buffer_data.append(f.read())
            else:
                self.buffer_data.append(self.gltf.binary_blob())

    # -------------------------------------------------------------
    # EXTRAER GEOMETRÍA
    # -------------------------------------------------------------
    def _accessor_data(self, index):
        acc = self.gltf.accessors[index]
        bv = self.gltf.bufferViews[acc.bufferView]
        buf = self.buffer_data[bv.buffer]

        dtype = np.float32
        comp = {"SCALAR": 1, "VEC2": 2, "VEC3": 3}.get(acc.type, 3)

        offset = (bv.byteOffset or 0) + (acc.byteOffset or 0)
        arr = np.frombuffer(buf, dtype=dtype, count=acc.count * comp, offset=offset)
        return arr.reshape((-1, comp))

    def _index_data(self, index):
        acc = self.gltf.accessors[index]
        bv = self.gltf.bufferViews[acc.bufferView]
        buf = self.buffer_data[bv.buffer]

        if acc.componentType == 5123:
            dtype = np.uint16
        elif acc.componentType == 5125:
            dtype = np.uint32
        else:
            dtype = np.uint8

        offset = (bv.byteOffset or 0) + (acc.byteOffset or 0)
        arr = np.frombuffer(buf, dtype=dtype, count=acc.count, offset=offset)
        return arr.astype(np.uint32)

    def _extract_mesh_data(self):
        print("📦 [Instanced] Extrayendo geometría GLB...")

        vertices_all = []
        uvs_all = []
        idx_all = []
        offset = 0

        for mesh in self.gltf.meshes:
            for prim in mesh.primitives:
                pos = self._accessor_data(prim.attributes.POSITION)
                uv = self._accessor_data(prim.attributes.TEXCOORD_0) \
                    if prim.attributes.TEXCOORD_0 is not None \
                    else np.zeros((len(pos), 2), dtype="f4")

                idx = self._index_data(prim.indices) if prim.indices else np.arange(len(pos))
                idx = idx + offset
                offset += len(pos)

                vertices_all.append(pos)
                uvs_all.append(uv)
                idx_all.append(idx)

        self.vertices = np.vstack(vertices_all)
        self.uvs = np.vstack(uvs_all)
        self.indices = np.hstack(idx_all)

        print(f"   ✔ Vértices: {len(self.vertices)}")
        print(f"   ✔ UVs: {len(self.uvs)}")
        print(f"   ✔ Índices: {len(self.indices)}")

    # -------------------------------------------------------------
    # TEXTURAS
    # -------------------------------------------------------------
    def _load_textures(self):
        print("🎨 [Instanced] Cargando textura baseColor...")

        self.texture = None
        if not self.gltf.materials:
            print("⚠ Modelo sin materiales.")
            return

        img = None
        try:
            mat = self.gltf.materials[0]
            mr = getattr(mat, "pbrMetallicRoughness", None)
            tex_index = None
            if mr and mr.baseColorTexture is not None:
                tex_index = mr.baseColorTexture.index

            if tex_index is not None:
                tex = self.gltf.textures[tex_index]
                img = self.gltf.images[tex.source]
        except Exception as e:
            print(f"⚠ No se pudo resolver baseColorTexture: {e}")

        if img is None:
            if not self.gltf.images:
                print("⚠ Modelo sin imágenes.")
                return
            print("⚠ Usando primera imagen del GLB.")
            img = self.gltf.images[0]

        if img.uri and img.uri.startswith("data:"):
            header, encoded = img.uri.split(",", 1)
            data = base64.b64decode(encoded)
            image = Image.open(io.BytesIO(data))
        elif img.bufferView is not None:
            bv = self.gltf.bufferViews[img.bufferView]
            buf = self.buffer_data[bv.buffer]
            offset = bv.byteOffset or 0
            data = buf[offset: offset + bv.byteLength]
            image = Image.open(io.BytesIO(data))
        else:
            print("⚠ No se encontró fuente de datos para textura.")
            return

        image = image.convert("RGBA")
        arr = np.array(image)

        self.texture = self.ctx.texture(arr.shape[1::-1], 4, arr.tobytes())
        self.texture.build_mipmaps()

    # -------------------------------------------------------------
    # MATRICES DE INSTANCIA
    # -------------------------------------------------------------
    def _create_instance_matrices(self):
        print("🧩 Creando matrices de instancia...")

        mats = []
        for inst in self.instances:
            pos = inst.get("pos", (0.0, 0.0, 0.0))
            rot = inst.get("rot", (0.0, 0.0, 0.0))
            scale = inst.get("scale", 1.0)

            # Normalizar scale a vec3
            if isinstance(scale, (int, float)):
                scale_vec = glm.vec3(scale, scale, scale)
            else:
                scale_vec = glm.vec3(*scale)

            m = glm.mat4()
            m = glm.translate(m, glm.vec3(*pos))
            m = glm.rotate(m, glm.radians(rot[0]), glm.vec3(1, 0, 0))
            m = glm.rotate(m, glm.radians(rot[1]), glm.vec3(0, 1, 0))
            m = glm.rotate(m, glm.radians(rot[2]), glm.vec3(0, 0, 1))
            m = glm.scale(m, scale_vec)

            mats.append(np.array(m.to_list(), dtype="f4"))

        if not mats:
            self.instance_matrices = np.zeros((0, 4, 4), dtype="f4")
            self.instance_count = 0
        else:
            self.instance_matrices = np.stack(mats, axis=0)
            self.instance_count = self.instance_matrices.shape[0]

        print(f"   ✔ Instancias: {self.instance_count}")

    # -------------------------------------------------------------
    # SHADER INSTANCIADO
    # -------------------------------------------------------------
    def _create_shader(self):
        self.shader = self.ctx.program(
            vertex_shader="""
                #version 330
                layout(location=0) in vec3 in_pos;
                layout(location=1) in vec2 in_uv;
                layout(location=2) in mat4 in_model;  // 16 floats, instanciado

                uniform mat4 m_proj;
                uniform mat4 m_view;

                out vec2 v_uv;

                void main() {
                    v_uv = in_uv;
                    gl_Position = m_proj * m_view * in_model * vec4(in_pos, 1.0);
                }
            """,
            fragment_shader="""
                #version 330
                uniform sampler2D tex0;
                in vec2 v_uv;
                out vec4 out_color;
                void main() {
                    out_color = texture(tex0, v_uv);
                }
            """
        )

    # -------------------------------------------------------------
    # BUFFERS (VBO + IBO + INSTANCE_VBO)
    # -------------------------------------------------------------
    def _create_buffers(self):
        # Buffer de vértices
        data = np.hstack([self.vertices, self.uvs]).astype("f4")
        self.vbo = self.ctx.buffer(data.tobytes())

        # Índices
        self.ibo = self.ctx.buffer(self.indices.astype("u4").tobytes())

        # Buffer de instancias (mat4 por instancia => 16 floats)
        if self.instance_count > 0:
            inst_bytes = self.instance_matrices.astype("f4").tobytes()
            self.instance_vbo = self.ctx.buffer(inst_bytes)
        else:
            self.instance_vbo = self.ctx.buffer(reserve=0)

        # VAO con atributo instanciado (16f/i => mat4 per instance)
        self.vao = self.ctx.vertex_array(
            self.shader,
            [
                (self.vbo, "3f 2f", "in_pos", "in_uv"),
                (self.instance_vbo, "16f/i", "in_model"),
            ],
            self.ibo
        )

    # -------------------------------------------------------------
    # COMPATIBILIDAD SceneManager
    # -------------------------------------------------------------
    def update_matrices(self):
        pass

    # -------------------------------------------------------------
    # RENDER
    # -------------------------------------------------------------
    def render(self):
        if self.instance_count == 0:
            return

        self.shader["m_proj"].write(self.app.camera.m_proj)
        self.shader["m_view"].write(self.app.camera.m_view)

        if self.texture:
            self.texture.use(0)
            self.shader["tex0"].value = 0

        self.vao.render(instances=self.instance_count)

    # -------------------------------------------------------------
    # CLEANUP
    # -------------------------------------------------------------
    def destroy(self):
        if self.vbo: self.vbo.release()
        if self.ibo: self.ibo.release()
        if self.instance_vbo: self.instance_vbo.release()
        if self.vao: self.vao.release()
        if self.texture: self.texture.release()
        if self.shader: self.shader.release()
