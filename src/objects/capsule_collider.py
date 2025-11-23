import glm


class CapsuleCollider:
    """
    Capsule Collider para representar el volumen físico del jugador.
    
    - No renderiza geometría (invisible)
    - Proporciona un AABB vertical para detección de colisiones
    - Compatible con el sistema try_move() de SceneManager
    - Representa un cilindro vertical con tapas hemisféricas
    
    Parámetros:
        radius: Radio de la cápsula (ancho del personaje)
        height: Altura total de la cápsula
        position: Posición del centro base de la cápsula
    """
    
    def __init__(self, radius=0.30, height=1.75, position=glm.vec3(0, 0, 0)):
        """
        Inicializa el CapsuleCollider.
        
        Args:
            radius: Radio horizontal del collider (default: 0.30m)
            height: Altura total del collider (default: 1.75m, altura humana)
            position: Posición inicial en el mundo (default: origen)
        """
        self.radius = radius
        self.height = height
        self.position = glm.vec3(position)
        
        # Cache del AABB local (se calcula una vez)
        self._aabb_local_cache = None
        
        print(f"✓ CapsuleCollider creado: radio={radius}m, altura={height}m")

    # ==================================================================
    # AABB LOCAL - Volumen de colisión
    # ==================================================================
    
    def aabb_local(self):
        """
        Devuelve el AABB local del collider en espacio de objeto.
        
        Representa un cilindro vertical:
        - Base centrada en (0, 0, 0)
        - Se extiende hacia arriba hasta self.height
        - Radio horizontal self.radius
        
        Returns:
            tuple: (min_vec3, max_vec3) en coordenadas locales
        """
        if self._aabb_local_cache is not None:
            return self._aabb_local_cache
        
        r = self.radius
        h = self.height
        
        # AABB que envuelve un cilindro vertical
        # Min: esquina inferior trasera izquierda
        # Max: esquina superior delantera derecha
        self._aabb_local_cache = (
            glm.vec3(-r, 0.0, -r),  # mínimo (base del cilindro)
            glm.vec3(+r, h, +r)     # máximo (tope del cilindro)
        )
        
        return self._aabb_local_cache

    # ==================================================================
    # TRANSFORMACIONES - Compatibilidad con SceneManager
    # ==================================================================
    
    def get_model_matrix(self):
        """
        Devuelve la matriz de modelo para transformar del espacio local al mundo.
        
        Para un capsule collider vertical simple, solo aplicamos traslación
        (sin rotación ni escala, ya que es simétrico).
        
        Returns:
            glm.mat4: Matriz de transformación 4x4
        """
        m = glm.mat4(1.0)  # Matriz identidad
        m = glm.translate(m, self.position)
        return m
    
    def get_position(self):
        """
        Obtiene la posición actual del collider.
        
        Returns:
            glm.vec3: Posición en el mundo
        """
        return self.position
    
    def set_position(self, xyz):
        """
        Establece la posición del collider.
        
        Args:
            xyz: Nueva posición como vec3, tupla o lista [x, y, z]
        """
        if isinstance(xyz, (tuple, list)):
            self.position = glm.vec3(*xyz)
        else:
            self.position = glm.vec3(xyz)

    # ==================================================================
    # INTERFAZ DE OBJETO 3D - Compatibilidad con el pipeline de render
    # ==================================================================
    
    def update_matrices(self):
        """
        Actualiza las matrices del objeto.
        No hace nada para un collider (no tiene shader).
        """
        pass
    
    def render(self):
        """
        Renderiza el objeto.
        El CapsuleCollider es invisible, así que no renderiza nada.
        """
        pass
    
    def destroy(self):
        """
        Libera recursos del collider.
        No tiene recursos GPU, así que no hace nada.
        """
        pass

    # ==================================================================
    # UTILIDADES ADICIONALES
    # ==================================================================
    
    def get_top_position(self):
        """
        Obtiene la posición del tope de la cápsula (útil para cámaras).
        
        Returns:
            glm.vec3: Posición de la parte superior de la cápsula
        """
        return glm.vec3(
            self.position.x,
            self.position.y + self.height,
            self.position.z
        )
    
    def get_center_position(self):
        """
        Obtiene la posición del centro geométrico de la cápsula.
        
        Returns:
            glm.vec3: Posición del centro
        """
        return glm.vec3(
            self.position.x,
            self.position.y + self.height * 0.5,
            self.position.z
        )
    
    def contains_point(self, point):
        """
        Verifica si un punto está dentro del volumen de la cápsula.
        
        Args:
            point: glm.vec3 o tupla (x, y, z)
            
        Returns:
            bool: True si el punto está dentro
        """
        if isinstance(point, (tuple, list)):
            point = glm.vec3(*point)
        
        # Verificar altura
        if point.y < self.position.y or point.y > self.position.y + self.height:
            return False
        
        # Verificar distancia horizontal al centro
        dx = point.x - self.position.x
        dz = point.z - self.position.z
        dist_sq = dx * dx + dz * dz
        
        return dist_sq <= self.radius * self.radius
    
    def sync_with_camera(self, camera):
        """
        Sincroniza la posición del collider con la cámara.
        Útil al cambiar de modo dios a primera persona.
        
        Args:
            camera: Objeto Camera con position (glm.vec3)
        """
        # Mantener el avatar en el suelo, usar solo X y Z de la cámara
        self.position.x = camera.position.x
        self.position.y = 0.01  # Ligeramente sobre el suelo para evitar colisiones con el piso
        self.position.z = camera.position.z
        
        print(f"   🔄 Avatar sincronizado: ({self.position.x:.2f}, {self.position.y:.2f}, {self.position.z:.2f})")
    
    def __repr__(self):
        """Representación en string para debugging."""
        return (f"CapsuleCollider(radius={self.radius}, height={self.height}, "
                f"position=({self.position.x:.2f}, {self.position.y:.2f}, {self.position.z:.2f}))")