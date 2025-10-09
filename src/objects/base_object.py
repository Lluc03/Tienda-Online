import moderngl as mgl
import glm
import numpy as np

class BaseObject:
    def __init__(self, app, shader_program=None):
        self.app = app
        self.ctx = app.ctx
        self.shader_program = shader_program or self.get_shader_program()
        self.vbo = self.get_vbo()
        self.vao = self.get_vao()
        self.m_model = self.get_model_matrix()
        self.on_init()
        
    def get_model_matrix(self):
        return glm.mat4()
        
    def on_init(self):
        self.shader_program['m_proj'].write(self.app.camera.m_proj)
        self.shader_program['m_view'].write(self.app.camera.m_view)
        self.shader_program['m_model'].write(self.m_model)

    def update_matrices(self):
        self.shader_program['m_proj'].write(self.app.camera.m_proj)
        self.shader_program['m_view'].write(self.app.camera.m_view)
        self.shader_program['m_model'].write(self.m_model)

    def render(self, mode=mgl.TRIANGLES):
        self.vao.render(mode=mode)
        
    def destroy(self):
        self.vbo.release()
        self.shader_program.release()
        self.vao.release()
    
    def get_vao(self):
        # Default implementation. If a subclass wants an specific one, create there
        vao = self.ctx.vertex_array(self.shader_program, [(self.vbo, '3f', 'in_position')])
        return vao
    
    def get_vertex_data(self):
        raise NotImplementedError("Subclasses must implement get_vertex_data")
    
    def get_vbo(self):
        vertex_data = self.get_vertex_data()
        return self.ctx.buffer(vertex_data)
    
    def get_shader_program(self):
        # Default basic shader
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