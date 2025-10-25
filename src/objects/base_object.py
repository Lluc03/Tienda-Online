import moderngl as mgl
import glm
import numpy as np
import pygame as pg

class BaseObject:
    def __init__(self, app, shader_program=None, texture_path=None, uv_scale=(1.0, 1.0)):
        self.app = app
        self.ctx = app.ctx
        self.texture = None
        self.uv_scale = uv_scale
        self.use_texture = texture_path is not None

        if self.use_texture:
            self.texture = self._load_texture(texture_path)

        self.shader_program = shader_program or self.get_shader_program()
        self.vbo = self.get_vbo()      # Subclase define layout (3f) o (3f,2f)
        self.vao = self.get_vao()      # Se arma según use_texture
        self.m_model = self.get_model_matrix()
        self.on_init()

    def _load_texture(self, path):
        surf = pg.image.load(path).convert_alpha()
        w, h = surf.get_size()
        data = pg.image.tostring(surf, 'RGBA', True)
        tex = self.ctx.texture((w, h), 4, data)
        tex.build_mipmaps()
        tex.filter = (mgl.LINEAR_MIPMAP_LINEAR, mgl.LINEAR)
        tex.repeat_x = True
        tex.repeat_y = True
        return tex

    def get_model_matrix(self):
        return glm.mat4()

    def on_init(self):
        self.shader_program['m_proj'].write(self.app.camera.m_proj)
        self.shader_program['m_view'].write(self.app.camera.m_view)
        self.shader_program['m_model'].write(self.m_model)
        if not self.use_texture and 'color' in self.shader_program:
            # Default color si la subclase no lo fija
            self.shader_program['color'].value = (0.8, 0.8, 0.8)

    def update_matrices(self):
        self.shader_program['m_proj'].write(self.app.camera.m_proj)
        self.shader_program['m_view'].write(self.app.camera.m_view)
        self.shader_program['m_model'].write(self.m_model)

    def render(self, mode=mgl.TRIANGLES):
        if self.use_texture and self.texture:
            self.texture.use(0)
            if 'tex0' in self.shader_program:
                self.shader_program['tex0'].value = 0
        self.vao.render(mode=mode)

    def destroy(self):
        self.vbo.release()
        self.shader_program.release()
        self.vao.release()

    def get_vao(self):
        if self.use_texture:
            vao = self.ctx.vertex_array(
                self.shader_program,                         
                [(self.vbo, '3f 2f', 'in_position', 'in_uv')]
            )
        else:
            vao = self.ctx.vertex_array(
                self.shader_program,                         
                [(self.vbo, '3f', 'in_position')]
            )
        return vao

    def get_vertex_data(self):
        raise NotImplementedError("Subclasses must implement get_vertex_data")

    def get_vbo(self):
        vertex_data = self.get_vertex_data()
        return self.ctx.buffer(vertex_data)

    def get_shader_program(self):
        if self.use_texture:
            return self.ctx.program(
                vertex_shader='''
                    #version 330
                    layout (location = 0) in vec3 in_position;
                    layout (location = 1) in vec2 in_uv;
                    uniform mat4 m_proj;
                    uniform mat4 m_view;
                    uniform mat4 m_model;
                    out vec2 v_uv;
                    void main() {
                        v_uv = in_uv;
                        gl_Position = m_proj * m_view * m_model * vec4(in_position, 1.0);
                    }
                ''',
                fragment_shader='''
                    #version 330
                    uniform sampler2D tex0;
                    in vec2 v_uv;
                    out vec4 fragColor;
                    void main() {
                        fragColor = texture(tex0, v_uv);
                    }
                '''
            )
        else:
            return self.ctx.program(
                vertex_shader='''
                    #version 330
                    layout (location = 0) in vec3 in_position;
                    uniform mat4 m_proj;
                    uniform mat4 m_view;
                    uniform mat4 m_model;
                    void main() {
                        gl_Position = m_proj * m_view * m_model * vec4(in_position, 1.0);
                    }
                ''',
                fragment_shader='''
                    #version 330
                    uniform vec3 color;
                    out vec4 fragColor;
                    void main() {
                        fragColor = vec4(color, 1.0);
                    }
                '''
            )
