import pygame
import os

backdrop = None
knob     = None 

class SliderRaton:
    def __init__(self, x, y, val_min, val_max, val_inicial, etiqueta):
        self.x_relativo = x  
        self.y          = y  
        self.alto       = 20
        self.val_min    = val_min
        self.val_max    = val_max
        self.val        = float(val_inicial)
        self.etiqueta   = etiqueta
        
        self.rect = pygame.Rect(x, y, 1289, self.alto) 
        self.tirador_ancho = 16
        self.tirador_rect = pygame.Rect(x, y, self.tirador_ancho, self.alto)
        self.arrastrando = False
        self.ultima_x_raton = 0
        self.actualizar_tirador_desde_val()

    def actualizar_tirador_desde_val(self):
        rango = self.val_max - self.val_min
        proporcion = (self.val - self.val_min) / rango if rango != 0 else 0
        self.tirador_rect.x = self.rect.x + int(proporcion * (self.rect.width - self.tirador_ancho))
        self.tirador_rect.y = self.y

    def manejar_evento(self, evento):
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if self.tirador_rect.collidepoint(evento.pos) or self.rect.collidepoint(evento.pos):
                self.arrastrando = True
                # CORREGIDO: Guardar solo la coordenada X en lugar de la tupla (x,y)
                self.ultima_x_raton = evento.pos[0]
                
                if not self.tirador_rect.collidepoint(evento.pos):
                    proporcion = (evento.pos[0] - self.rect.x) / (self.rect.width - self.tirador_ancho)
                    self.val = self.val_min + proporcion * (self.val_max - self.val_min)
                    self.actualizar_tirador_desde_val()
                return True
                
        elif evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
            self.arrastrando = False
            
        elif evento.type == pygame.MOUSEMOTION and self.arrastrando:
            # CORREGIDO: Extraer la componente X de la posición actual del ratón
            x_actual = evento.pos[0]
            delta_x = x_actual - self.ultima_x_raton
            self.ultima_x_raton = x_actual
            
            if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                factor_sensibilidad = 0.1
            else:
                factor_sensibilidad = 1.0
                
            unidades_por_pixel = (self.val_max - self.val_min) / (self.rect.width - self.tirador_ancho)
            self.val += delta_x * unidades_por_pixel * factor_sensibilidad
            
            if self.val < self.val_min: self.val = self.val_min
            if self.val > self.val_max: self.val = self.val_max
            
            self.actualizar_tirador_desde_val()
            return True
            
        return False

    def dibujar(self, superficie, fuente, fuente_lcd):
        # pygame.draw.rect(superficie, (60, 60, 75), self.rect, border_radius=4)
        color_tirador = (50, 220, 120,64) if self.arrastrando else (50, 120, 240)
        pygame.draw.rect(superficie, color_tirador, self.tirador_rect, border_radius=4)
        superficie.blit(knob, (self.tirador_rect.x, self.tirador_rect.y-6))
        txt = fuente    .render(f"{self.etiqueta}", True, (255, 255, 255))
        val = fuente_lcd.render(f"{str(int(self.val)).rjust(8)}", True, (255, 55, 0))
        superficie.blit(txt, (self.rect.x-128, self.rect.y))
        superficie.blit(val, (self.rect.x+self.rect.w+13, self.rect.y - 1))

def carga_imagen(ruta_imagen):
    if ruta_imagen and os.path.exists(ruta_imagen):
        try:
            return pygame.image.load(ruta_imagen).convert_alpha()            
        except Exception as e:
            print(f"[Aviso] No se pudo cargar el backdrop: {e}")
            exit(1)
    
def mostrar_splash(pantalla, ancho, alto):
    global backdrop
    global knob
    pantalla.fill((20, 20, 25))
    fuente_splash = pygame.font.SysFont("Consolas", 28, bold=True)
    fuente_sub = pygame.font.SysFont("Consolas", 16)
    
    backdrop = carga_imagen('deck.png')
    knob     = carga_imagen('knob.png')
    pantalla.blit(backdrop, (0, 0))
        
    txt_titulo = fuente_splash.render("LOOPXPORT PRO", True, (130, 250, 50))
    txt_carga = fuente_sub.render("Decodificando audio y fijando geometría sólida estable... Espere.", True, (130, 250, 50))
    pantalla.blit(txt_titulo, (ancho // 2 - txt_titulo.get_width() // 2, alto // 3 - 40))
    pantalla.blit(txt_carga, (ancho // 2 - txt_carga.get_width() // 2, alto // 3 + 10))
    pygame.display.flip()


def dibujar_onda_y_aguja(pantalla, audio_g, max_amplitud_global, inicio_muestras, muestras_actuales, posicion_aguja, ancho_w, alto_w):
    global backdrop
    pantalla.blit(backdrop, (0, 0))
    origen_x        , origen_y      =  109, 121
    ancho_grafica   , alto_grafica  = 1476, 394
    
    
    linea_central_y = origen_y + (alto_grafica // 2)

    inicio_muestras = int(inicio_muestras)
    muestras_actuales = int(muestras_actuales)

    # FIJAR LA ONDA PARA QUE NO OSCILE NI CAMBIE DE FORMA AL MOVER EL ZOOM/PERIODO
    # Mapeamos los píxeles usando una cuadrícula matemática rígida independiente de los decimales de la UI
    paso_muestras_por_pixel = muestras_actuales / ancho_grafica
    for x_pixel in range(ancho_grafica):
        # Mapeo directo y redondeado a enteros de forma uniforme para estabilizar los picos
        desplazamiento_muestras = int(x_pixel * paso_muestras_por_pixel)
        idx_muestra_global = inicio_muestras + desplazamiento_muestras
        
        if idx_muestra_global < len(audio_g):
            valor_muestra = audio_g[idx_muestra_global]
            
            if max_amplitud_global > 0:
                valor_normalizado = valor_muestra / max_amplitud_global
            else:
                valor_normalizado = valor_muestra
                
            semi_altura_barra = int(abs(valor_normalizado) * (alto_grafica / 2) * 0.95)
            if semi_altura_barra > 0:
                y_superior = linea_central_y - semi_altura_barra
                y_inferior = linea_central_y + semi_altura_barra
                
                factor_color = min(1.0, abs(valor_normalizado) * 1.2)
                r = int(100 + (60 * factor_color))     
                g = int(200 + (55 * factor_color))
                b = int(40 + (10 * factor_color))
                
                pygame.draw.line(pantalla, (r, g, b), (origen_x + x_pixel, y_superior), (origen_x + x_pixel, y_inferior), 1)

    pygame.draw.line(pantalla, (255, 255, 55), (origen_x, linea_central_y), (origen_x + ancho_grafica, linea_central_y), 1)

    # Dibujar la aguja de reproducción basándonos en la misma proporción estable
    if inicio_muestras <= posicion_aguja <= (inicio_muestras + muestras_actuales):
        porcentaje_aguja = (posicion_aguja - inicio_muestras) / muestras_actuales
        x_aguja = origen_x + int(porcentaje_aguja * ancho_grafica)
        pygame.draw.line(pantalla, (255, 50, 50), (x_aguja, origen_y), (x_aguja, origen_y + alto_grafica), 2)
