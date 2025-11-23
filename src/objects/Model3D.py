import glm
import numpy as np
import base64
import os
from pygltflib import GLTF2
from PIL import Image
import io


class Model3D:
    """
    Cargador GLB ultrasimple para evitar errores de materiales y shaders.
    - Carga POS + UV + INDICES
    - Usa 1 textura baseColor (si existe)
    - Shader extremadamente simple (position + uv + sampler2D)
    """

    def __init__(self, app, model_path, position=glm.vec3(0, 0, 0),
                 scale=glm.vec3(1, 1, 1), rotation=(0, 0, 0)):

        self.app = app
        self.ctx = app.ctx

        self.model_path = model_path
        self.model_dir = os.path.dirname(model_path)

        self.position = glm.vec3(position)
        self.scale = glm.vec3(scale)
        self.rotation = rotation

        # Datos GLTF
        self.gltf = None
        self.buffer_data = []

        # Geometría
        self.vertices = None
        self.uvs = None
        self.indices = None

        # AABB local cache
        self._aabb_local = None

        # GPU resources
        self.vbo = None
        self.ibo = None
        self.vao = None
        self.texture = None
        self.shader = None

        # Load stages
        self._load_gltf()
        self._extract_mesh_data()
        self._load_textures()
        self._create_shader()
        self._create_buffers()

    # -------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------
    def get_position(self):
        return self.position

    def set_position(self, xyz):
        self.position = glm.vec3(*xyz)

    def set_scale(self, xyz):
        self.scale = glm.vec3(*xyz)

    def set_rotation(self, deg_tuple):
        # deg_tuple = (pitch, yaw, roll)
        self.rotation = deg_tuple

    # -------------------------------------------------------------
    # AABB LOCAL PARA COLISIONES
    # -------------------------------------------------------------
    def aabb_local(self):
        """
        Devuelve el AABB local del modelo basándose en self.vertices.
        SceneManager.try_move() usa este volumen para colisiones.
        """
        if self._aabb_local is not None:
            return self._aabb_local

        if self.vertices is None or len(self.vertices) == 0:
            return None

        mins = self.vertices.min(axis=0)
        maxs = self.vertices.max(axis=0)

        # DEVOLVER glm.vec3, NO TUPLAS
        self._aabb_local = (
            glm.vec3(float(mins[0]), float(mins[1]), float(mins[2])),
            glm.vec3(float(maxs[0]), float(maxs[1]), float(maxs[2])),
        )
        return self._aabb_local


    # -------------------------------------------------------------
    # CARGA GLB
    # -------------------------------------------------------------
    def _load_gltf(self):
        print(f"🔍 Cargando GLB: {self.model_path}")
        self.gltf = GLTF2().load(self.model_path)

        # Cargar buffers binarios
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
        print("📦 Extrayendo geometría GLB...")

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
        print("🎨 Cargando textura baseColor desde el material...")

        self.texture = None

        if not self.gltf.materials:
            print("⚠ Modelo sin materiales. No hay baseColorTexture.")
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
            print(f"⚠ No se pudo resolver baseColorTexture desde el material: {e}")

        if img is None:
            if not self.gltf.images:
                print("⚠ Modelo sin imágenes. No hay textura.")
                return
            print("⚠ Material sin baseColorTexture; usando la primera imagen del GLB.")
            img = self.gltf.images[0]

        # Leer image embebida o desde bufferView
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
            print("⚠ No se encontró imagen válida.")
            return

        image = image.convert("RGBA")
        arr = np.array(image)

        self.texture = self.ctx.texture(arr.shape[1::-1], 4, arr.tobytes())
        self.texture.build_mipmaps()

    # -------------------------------------------------------------
    # SHADER SIMPLE
    # -------------------------------------------------------------
    def _create_shader(self):
        self.shader = self.ctx.program(
            vertex_shader="""
                #version 330
                layout(location=0) in vec3 in_pos;
                layout(location=1) in vec2 in_uv;
                uniform mat4 m_proj;
                uniform mat4 m_view;
                uniform mat4 m_model;
                out vec2 v_uv;
                void main() {
                    v_uv = in_uv;
                    gl_Position = m_proj * m_view * m_model * vec4(in_pos, 1.0);
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
    # BUFFERS
    # -------------------------------------------------------------
    def _create_buffers(self):
        data = np.hstack([self.vertices, self.uvs]).astype("f4")

        self.vbo = self.ctx.buffer(data.tobytes())
        self.ibo = self.ctx.buffer(self.indices.astype("u4").tobytes())

        self.vao = self.ctx.vertex_array(
            self.shader,
            [(self.vbo, "3f 2f", "in_pos", "in_uv")],
            self.ibo
        )

    # -------------------------------------------------------------
    # MATRIZ DE MODELO
    # -------------------------------------------------------------
    def get_model_matrix(self):
        m = glm.mat4()
        m = glm.translate(m, self.position)
        m = glm.rotate(m, glm.radians(self.rotation[0]), glm.vec3(1, 0, 0))
        m = glm.rotate(m, glm.radians(self.rotation[1]), glm.vec3(0, 1, 0))
        m = glm.rotate(m, glm.radians(self.rotation[2]), glm.vec3(0, 0, 1))
        m = glm.scale(m, self.scale)
        return m

    # -------------------------------------------------------------
    # COMPATIBILIDAD CON SCENEMANAGER
    # -------------------------------------------------------------
    def update_matrices(self):
        pass  # No hace falta para GLB simple

    # -------------------------------------------------------------
    # RENDER
    # -------------------------------------------------------------
    def render(self):
        self.shader["m_proj"].write(self.app.camera.m_proj)
        self.shader["m_view"].write(self.app.camera.m_view)
        self.shader["m_model"].write(self.get_model_matrix())

        if self.texture:
            self.texture.use(0)
            self.shader["tex0"].value = 0

        self.vao.render()

    # -------------------------------------------------------------
    # CLEANUP
    # -------------------------------------------------------------
    def destroy(self):
        if self.vbo: self.vbo.release()
        if self.ibo: self.ibo.release()
        if self.vao: self.vao.release()
        if self.texture: self.texture.release()
        if self.shader: self.shader.release()
