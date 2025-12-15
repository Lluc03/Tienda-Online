import glm
import numpy as np
import base64
import os
from pygltflib import GLTF2
from PIL import Image
import io


class Model3DMultiMaterial:
    """
    Loader GLB para modelos complejos con múltiples materiales.
    - 1 objeto lógico
    - N submeshes
    - N texturas
    """

    def __init__(self, app, model_path,
                 position=glm.vec3(0, 0, 0),
                 scale=glm.vec3(1, 1, 1),
                 rotation=(0, 0, 0)):

        self.app = app
        self.ctx = app.ctx

        self.model_path = model_path
        self.model_dir = os.path.dirname(model_path)

        self.position = glm.vec3(position)
        self.scale = glm.vec3(scale)
        self.rotation = rotation

        # GLTF
        self.gltf = None
        self.buffer_data = []

        # Submeshes
        self.submeshes = []  # [{vao, ibo, texture, index_count}]

        self.shader = None
        self._aabb_local = None

        self._load_gltf()
        self._create_shader()
        self._extract_submeshes()

    # --------------------------------------------------
    # GLTF
    # --------------------------------------------------
    def _load_gltf(self):
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

    # --------------------------------------------------
    # Accesores
    # --------------------------------------------------
    def _accessor(self, idx):
        acc = self.gltf.accessors[idx]
        bv = self.gltf.bufferViews[acc.bufferView]
        buf = self.buffer_data[bv.buffer]

        comp = {"SCALAR": 1, "VEC2": 2, "VEC3": 3}[acc.type]
        offset = (bv.byteOffset or 0) + (acc.byteOffset or 0)

        arr = np.frombuffer(
            buf, dtype=np.float32,
            count=acc.count * comp,
            offset=offset
        )
        return arr.reshape((-1, comp))

    def _indices(self, idx):
        acc = self.gltf.accessors[idx]
        bv = self.gltf.bufferViews[acc.bufferView]
        buf = self.buffer_data[bv.buffer]

        dtype = {5123: np.uint16, 5125: np.uint32}.get(acc.componentType, np.uint8)
        offset = (bv.byteOffset or 0) + (acc.byteOffset or 0)

        arr = np.frombuffer(buf, dtype=dtype, count=acc.count, offset=offset)
        return arr.astype(np.uint32)

    # --------------------------------------------------
    # Texturas
    # --------------------------------------------------
    def _load_texture_from_material(self, mat_index):
        if mat_index is None or mat_index >= len(self.gltf.materials):
            return None

        mat = self.gltf.materials[mat_index]
        mr = mat.pbrMetallicRoughness
        if not mr or not mr.baseColorTexture:
            return None

        tex = self.gltf.textures[mr.baseColorTexture.index]
        img = self.gltf.images[tex.source]

        if img.uri and img.uri.startswith("data:"):
            data = base64.b64decode(img.uri.split(",", 1)[1])
            image = Image.open(io.BytesIO(data))
        elif img.bufferView is not None:
            bv = self.gltf.bufferViews[img.bufferView]
            buf = self.buffer_data[bv.buffer]
            data = buf[bv.byteOffset: bv.byteOffset + bv.byteLength]
            image = Image.open(io.BytesIO(data))
        else:
            return None

        image = image.convert("RGBA")
        arr = np.array(image)

        tex = self.ctx.texture(arr.shape[1::-1], 4, arr.tobytes())
        tex.build_mipmaps()
        return tex

    # --------------------------------------------------
    # Submeshes
    # --------------------------------------------------
    def _extract_submeshes(self):
        for mesh in self.gltf.meshes:
            for prim in mesh.primitives:
                pos = self._accessor(prim.attributes.POSITION)
                uv = self._accessor(prim.attributes.TEXCOORD_0)
                idx = self._indices(prim.indices)

                data = np.hstack([pos, uv]).astype("f4")
                vbo = self.ctx.buffer(data.tobytes())
                ibo = self.ctx.buffer(idx.tobytes())

                vao = self.ctx.vertex_array(
                    self.shader,
                    [(vbo, "3f 2f", "in_pos", "in_uv")],
                    ibo
                )

                tex = self._load_texture_from_material(prim.material)

                self.submeshes.append({
                    "vao": vao,
                    "ibo": ibo,
                    "texture": tex,
                    "count": len(idx)
                })

    # --------------------------------------------------
    # Shader
    # --------------------------------------------------
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

    # --------------------------------------------------
    # Transform
    # --------------------------------------------------
    def get_model_matrix(self):
        m = glm.mat4()
        m = glm.translate(m, self.position)
        m = glm.rotate(m, glm.radians(self.rotation[0]), glm.vec3(1, 0, 0))
        m = glm.rotate(m, glm.radians(self.rotation[1]), glm.vec3(0, 1, 0))
        m = glm.rotate(m, glm.radians(self.rotation[2]), glm.vec3(0, 0, 1))
        m = glm.scale(m, self.scale)
        return m
    
    def update_matrices(self):
        pass


    # --------------------------------------------------
    # Render
    # --------------------------------------------------
    def render(self):
        self.shader["m_proj"].write(self.app.camera.m_proj)
        self.shader["m_view"].write(self.app.camera.m_view)
        self.shader["m_model"].write(self.get_model_matrix())

        for sm in self.submeshes:
            if sm["texture"]:
                sm["texture"].use(0)
                self.shader["tex0"].value = 0
            sm["vao"].render()

    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------
    def destroy(self):
        for sm in self.submeshes:
            sm["vao"].release()
            sm["ibo"].release()
            if sm["texture"]:
                sm["texture"].release()
        self.shader.release()
