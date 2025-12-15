import glm
import numpy as np
import base64
import os
from pygltflib import GLTF2
from PIL import Image
import io


class InstancedModel3D:
    """
    Cargador GLB con instanciado múltiple para renderizar muchas copias eficientemente.
    
    Características:
    - Carga geometría desde GLB una sola vez
    - Renderiza múltiples instancias con diferentes posiciones/rotaciones
    - Soporte para hover (iluminación al pasar el ratón)
    - Sistema de detección para raycast
    - Optimizado para productos en supermercados
    
    Uso:
        instances = [
            {"pos": (1, 0, 1), "rot": (0, 45, 0), "scale": (1, 1, 1)},
            {"pos": (2, 0, 1), "rot": (0, 0, 0), "scale": (1, 1, 1)},
        ]
        water_bottles = InstancedModel3D(app, "water.glb", instances)
    """

    def __init__(self, app, model_path, instances):
        """
        Inicializa el modelo instanciado.
        
        Args:
            app: Aplicación principal con contexto OpenGL
            model_path: Ruta al archivo GLB
            instances: Lista de diccionarios con 'pos', 'rot', 'scale'
        """
        self.app = app
        self.ctx = app.ctx

        self.model_path = model_path
        self.model_dir = os.path.dirname(model_path)

        # Instancias (posiciones, rotaciones, escalas)
        self.instances = instances
        self.instance_count = len(instances)

        # Datos GLTF
        self.gltf = None
        self.buffer_data = []

        # Geometría base
        self.vertices = None
        self.uvs = None
        self.indices = None

        # AABB local cache
        self._aabb_local = None

        # GPU resources
        self.vbo = None
        self.instance_vbo = None
        self.ibo = None
        self.vao = None
        self.texture = None
        self.shader = None

        # ===== Sistema de hover POR INSTANCIA =====
        self.is_hovered = False
        self.hovered_instance_id = -1  # ID de la instancia específica en hover
        self.hover_color = glm.vec3(1.5, 1.5, 1.0)  # Amarillo brillante
        
        # Identificador de tipo de producto
        self.product_type = self._get_product_type_from_path(model_path)

        # Transformación base
        self.position = glm.vec3(0, 0, 0)
        self.scale = glm.vec3(1, 1, 1)
        self.rotation = (0, 0, 0)

        # Cargar el modelo
        self._load_gltf()
        self._extract_mesh_data()
        self._load_textures()
        self._create_shader()
        self._create_buffers()

        print(f"✓ InstancedModel3D cargado: {self.instance_count} instancias de {os.path.basename(model_path)}")
        print(f"  Tipo de producto: {self.product_type}")

    # ================================================================
    # IDENTIFICACIÓN DE PRODUCTO
    # ================================================================
    
    def _get_product_type_from_path(self, path):
        filename = os.path.basename(path).lower()

        if "water" in filename:
            return "water"
        elif "chips" in filename:
            return "chips"
        elif "milk" in filename:
            return "milk"
        elif "apple" in filename:
            return "apple"
        elif "orange" in filename:
            return "orange"
        elif "kinder" in filename:
            return "kinder"
        elif "tuna" in filename:
            return "tuna"
        elif "cereal" in filename:
            return "cereals"
        elif "wine" in filename:
            return "wine"
        elif "coke" in filename or "coca" in filename:
            return "cocacola"
        elif "cava" in filename or "champagne" in filename:
            return "cava"
        elif "whiskey" in filename:
            return "whiskey"
        elif "paper" in filename:
            return "paper"
        elif "shampoo" in filename:
            return "shampoo"
        elif "sponge" in filename:
            return "sponge"
        elif "candle" in filename:
            return "candle"
        elif "jarron" in filename:
            return "jarron"
        elif "mug" in filename:
            return "mug"
        else:
            return "unknown"


    # ================================================================
    # CARGA DE GLTF
    # ================================================================

    def _load_gltf(self):
        """Carga el archivo GLB y sus buffers binarios."""
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

    # ================================================================
    # EXTRACCIÓN DE GEOMETRÍA
    # ================================================================

    def _accessor_data(self, index):
        """Lee datos de un accessor GLTF."""
        acc = self.gltf.accessors[index]
        bv = self.gltf.bufferViews[acc.bufferView]

        buf = self.buffer_data[bv.buffer]

        dtype = np.float32
        comp = {"SCALAR": 1, "VEC2": 2, "VEC3": 3}.get(acc.type, 3)

        offset = (bv.byteOffset or 0) + (acc.byteOffset or 0)
        arr = np.frombuffer(buf, dtype=dtype, count=acc.count * comp, offset=offset)
        return arr.reshape((-1, comp))

    def _index_data(self, index):
        """Lee índices de un accessor GLTF."""
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
        """Extrae vértices, UVs e índices del modelo."""
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

    # ================================================================
    # TEXTURAS
    # ================================================================

    def _load_textures(self):
        """Carga la textura baseColor del material."""
        self.texture = None

        if not self.gltf.materials:
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
        except Exception:
            pass

        if img is None:
            if not self.gltf.images:
                return
            img = self.gltf.images[0]

        # Leer imagen
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
            return

        image = image.convert("RGBA")
        arr = np.array(image)

        self.texture = self.ctx.texture(arr.shape[1::-1], 4, arr.tobytes())
        self.texture.build_mipmaps()

    # ================================================================
    # SHADER CON INSTANCING Y HOVER
    # ================================================================

    def _create_shader(self):
        """Crea shader con soporte para instancing y highlighting."""
        self.shader = self.ctx.program(
            vertex_shader="""
                #version 330
                layout(location=0) in vec3 in_pos;
                layout(location=1) in vec2 in_uv;
                layout(location=2) in vec3 in_offset;
                layout(location=3) in vec3 in_rotation;
                layout(location=4) in vec3 in_scale;
                
                uniform mat4 m_proj;
                uniform mat4 m_view;
                uniform mat4 m_model;
                
                out vec2 v_uv;
                out vec3 v_world_pos;
                out float v_instance_id;
                
                mat4 rotationMatrix(vec3 axis, float angle) {
                    axis = normalize(axis);
                    float s = sin(angle);
                    float c = cos(angle);
                    float oc = 1.0 - c;
                    
                    return mat4(
                        oc * axis.x * axis.x + c,           oc * axis.x * axis.y - axis.z * s,  oc * axis.z * axis.x + axis.y * s,  0.0,
                        oc * axis.x * axis.y + axis.z * s,  oc * axis.y * axis.y + c,           oc * axis.y * axis.z - axis.x * s,  0.0,
                        oc * axis.z * axis.x - axis.y * s,  oc * axis.y * axis.z + axis.x * s,  oc * axis.z * axis.z + c,           0.0,
                        0.0,                                0.0,                                0.0,                                1.0
                    );
                }
                
                void main() {
                    v_instance_id = float(gl_InstanceID);
                    
                    // 1. Aplicar escala primero
                    vec3 scaled_pos = in_pos * in_scale;
                    
                    // 2. Aplicar rotación (Euler angles en grados) - Orden YXZ para coincidir con glm
                    mat4 rotX = rotationMatrix(vec3(1.0, 0.0, 0.0), radians(in_rotation.x));
                    mat4 rotY = rotationMatrix(vec3(0.0, 1.0, 0.0), radians(in_rotation.y));
                    mat4 rotZ = rotationMatrix(vec3(0.0, 0.0, 1.0), radians(in_rotation.z));
                    
                    // Orden común: Y (yaw) -> X (pitch) -> Z (roll)
                    mat4 rotation = rotX * rotZ * rotY;
                    
                    vec4 rotated_pos = rotation * vec4(scaled_pos, 1.0);
                    
                    // 3. Aplicar traslación (offset) - SOLO después de escala y rotación
                    vec3 final_pos = rotated_pos.xyz + in_offset;
                    
                    // 4. Aplicar matriz de modelo global (si hay)
                    vec4 world_pos = m_model * vec4(final_pos, 1.0);
                    
                    v_world_pos = world_pos.xyz;
                    v_uv = in_uv;
                    gl_Position = m_proj * m_view * world_pos;
                }
            """,
            fragment_shader="""
                #version 330
                uniform sampler2D tex0;
                uniform bool u_hovered;
                uniform vec3 u_hover_color;
                uniform int u_hovered_instance;
                
                in vec2 v_uv;
                in vec3 v_world_pos;
                in float v_instance_id;
                out vec4 out_color;
                
                void main() {
                    vec4 tex_color = texture(tex0, v_uv);
                    
                    // Iluminar solo la instancia específica que está en hover
                    if (u_hovered && int(v_instance_id) == u_hovered_instance) {
                        out_color = vec4(tex_color.rgb * u_hover_color, tex_color.a);
                    } else {
                        out_color = tex_color;
                    }
                }
            """
        )

    # ================================================================
    # BUFFERS
    # ================================================================

    def _create_buffers(self):
        """Crea VBO/IBO incluyendo datos de instancing."""
        # VBO principal: vertices + UVs
        data = np.hstack([self.vertices, self.uvs]).astype("f4")
        self.vbo = self.ctx.buffer(data.tobytes())

        # VBO de instancing: offsets + rotations + scales
        instance_data = []
        for inst in self.instances:
            pos = inst.get("pos", (0, 0, 0))
            rot = inst.get("rot", (0, 0, 0))
            scale = inst.get("scale", (1, 1, 1))
            
            # Normalizar valores a tuplas
            if isinstance(pos, (int, float)):
                pos = (pos, pos, pos)
            if isinstance(rot, (int, float)):
                rot = (rot, rot, rot)
            if isinstance(scale, (int, float)):
                scale = (scale, scale, scale)
            
            instance_data.append([
                pos[0], pos[1], pos[2],      # offset
                rot[0], rot[1], rot[2],      # rotation
                scale[0], scale[1], scale[2] # scale
            ])
        
        instance_array = np.array(instance_data, dtype="f4")
        self.instance_vbo = self.ctx.buffer(instance_array.tobytes())

        # IBO
        self.ibo = self.ctx.buffer(self.indices.astype("u4").tobytes())

        # VAO
        self.vao = self.ctx.vertex_array(
            self.shader,
            [
                (self.vbo, "3f 2f", "in_pos", "in_uv"),
                (self.instance_vbo, "3f 3f 3f/i", "in_offset", "in_rotation", "in_scale"),
            ],
            self.ibo
        )

    # ================================================================
    # AABB PARA COLISIONES
    # ================================================================

    def aabb_local(self):
        """
        Devuelve el AABB local de UNA instancia del modelo.
        Para picking, SceneManager debe transformar esto por cada instancia.
        """
        if self._aabb_local is not None:
            return self._aabb_local

        if self.vertices is None or len(self.vertices) == 0:
            return None

        mins = self.vertices.min(axis=0)
        maxs = self.vertices.max(axis=0)

        self._aabb_local = (
            glm.vec3(float(mins[0]), float(mins[1]), float(mins[2])),
            glm.vec3(float(maxs[0]), float(maxs[1]), float(maxs[2])),
        )
        return self._aabb_local

    # ================================================================
    # TRANSFORMACIONES
    # ================================================================

    def get_model_matrix(self):
        """Matriz de modelo base (antes de aplicar offsets de instancias)."""
        m = glm.mat4()
        m = glm.translate(m, self.position)
        m = glm.rotate(m, glm.radians(self.rotation[0]), glm.vec3(1, 0, 0))
        m = glm.rotate(m, glm.radians(self.rotation[1]), glm.vec3(0, 1, 0))
        m = glm.rotate(m, glm.radians(self.rotation[2]), glm.vec3(0, 0, 1))
        m = glm.scale(m, self.scale)
        return m

    def get_position(self):
        return self.position

    def set_position(self, xyz):
        self.position = glm.vec3(*xyz)

    # ================================================================
    # HOVER SYSTEM
    # ================================================================

    def set_hovered(self, hovered, instance_id=-1):
        """
        Activa/desactiva el estado de hover para una instancia específica.
        
        Args:
            hovered (bool): True si el ratón está sobre el producto
            instance_id (int): ID de la instancia específica (0 a N-1), -1 para todas
        """
        self.is_hovered = hovered
        self.hovered_instance_id = instance_id if hovered else -1

    # ================================================================
    # COMPATIBILIDAD CON SCENEMANAGER
    # ================================================================

    def update_matrices(self):
        """No hace falta para instanced rendering."""
        pass

    # ================================================================
    # RENDER
    # ================================================================

    def render(self):
        """Renderiza todas las instancias con un solo draw call."""
        self.shader["m_proj"].write(self.app.camera.m_proj)
        self.shader["m_view"].write(self.app.camera.m_view)
        self.shader["m_model"].write(self.get_model_matrix())

        # Pasar estado de hover al shader
        self.shader["u_hovered"].value = self.is_hovered
        self.shader["u_hovered_instance"].value = self.hovered_instance_id
        self.shader["u_hover_color"].write(self.hover_color)

        if self.texture:
            self.texture.use(0)
            self.shader["tex0"].value = 0

        # Render instanciado
        self.vao.render(instances=self.instance_count)

    # ================================================================
    # CLEANUP
    # ================================================================

    def destroy(self):
        """Libera recursos GPU."""
        if self.vbo: self.vbo.release()
        if self.instance_vbo: self.instance_vbo.release()
        if self.ibo: self.ibo.release()
        if self.vao: self.vao.release()
        if self.texture: self.texture.release()
        if self.shader: self.shader.release()

    # ================================================================
    # UTILIDADES
    # ================================================================

    def __repr__(self):
        return (f"InstancedModel3D(product_type='{self.product_type}', "
                f"instances={self.instance_count}, "
                f"hovered={self.is_hovered})")