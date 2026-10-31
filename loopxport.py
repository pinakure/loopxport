import logo
# --- TRUCO DE COMPATIBILIDAD PYTHON 3.13 ---
import sys
try:
    import audioop
except ImportError:
    import audioop_lts as audioop
sys.modules['audioop'] = audioop
sys.modules['pyaudioop'] = audioop
# --------------------------------------------

import numpy as np
import pygame
import time

import ui
import filesys
import audio 
import os

def main(archivo_entrada, intervalo=None, offset=0.0):
    pygame.init()
    pygame.font.init()
    
    ANCHO, ALTO = 1650, 928 
    pantalla = pygame.display.set_mode((ANCHO, ALTO), pygame.NOFRAME)
    pygame.display.set_caption(f"LoopXPort Pro - { archivo_entrada.split(os.path.sep)[-1] }")
    
    ui.mostrar_splash(pantalla, ANCHO, ALTO)
    
    audio_g, audio_rep, fps, canales, audio_seg = audio.cargar_audio(archivo_entrada)
    total_muestras = len(audio_g)
    
    max_amplitud_global = np.max(np.abs(audio_g))
    if max_amplitud_global == 0: max_amplitud_global = 1.0

    stream = audio.inicializar_motor(audio_rep, fps, canales)

    fuente          = pygame.font.Font(filesys.path("ocr.ttf"), 16)
    fuente_lcd      = pygame.font.Font(filesys.path("lcd.ttf"), 24)
    reloj           = pygame.time.Clock()

    bpm_actual      = 128.0
    tiempos_actuales = 16
    duracion_s      = tiempos_actuales / (bpm_actual / 60.0) 
    muestras_actuales = float(int(duracion_s * fps)) if intervalo is None else float(intervalo)
    
    offset_inicial_muestras = float(offset)
    bloque_seleccionado = 1

    # REQUERIMIENTO 1: El límite máximo de offset ahora permite descartar bloques completos y secciones enteras (hasta la mitad de la canción)
    limite_max_offset = int(total_muestras // 2)

    slider_offset   = ui.SliderRaton(192, 573, 0, limite_max_offset, offset_inicial_muestras, "Offset") 
    slider_general  = ui.SliderRaton(192, 624, 1000, int(total_muestras // 2), muestras_actuales, "Interval")
    slider_fino     = ui.SliderRaton(192, 676, muestras_actuales - 500, muestras_actuales + 500, muestras_actuales, "Fine Adjust")
    slider_bloque   = ui.SliderRaton(192, 727, 1, 2, 1, "Block")

    ejecutando = True
    while ejecutando:
        reloj.tick(60)
        ancho_w, alto_w = pantalla.get_size()
        
        offset_actual = int(slider_offset.val)
        
        muestras_utiles = total_muestras - offset_actual
        num_bloques = int(muestras_utiles // int(muestras_actuales))
        if num_bloques < 1: num_bloques = 1
        slider_bloque.val_max = num_bloques
        
        if bloque_seleccionado > num_bloques:
            bloque_seleccionado = num_bloques
            slider_bloque.val = float(num_bloques)
            slider_bloque.actualizar_tirador_desde_val()
        
        inicio_bloque_muestras = offset_actual + (bloque_seleccionado - 1) * int(muestras_actuales)
        bpm_real = (tiempos_actuales * fps * 60.0) / muestras_actuales

        # --- EVENTOS ---
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False
            
            elif evento.type == pygame.VIDEORESIZE:
                ancho_w, alto_w = evento.size
                pantalla = pygame.display.set_mode((ancho_w, alto_w), pygame.RESIZABLE)
                slider_offset.recalcular_dimensiones(ancho_w, alto_w)
                slider_general.recalcular_dimensiones(ancho_w, alto_w)
                slider_fino.recalcular_dimensiones(ancho_w, alto_w)
                slider_bloque.recalcular_dimensiones(ancho_w, alto_w)

            if slider_offset.manejar_evento(evento):
                offset_actual = int(slider_offset.val)
                inicio_bloque_muestras = offset_actual + (bloque_seleccionado - 1) * int(muestras_actuales)
                audio.actualizar_parametros_dinamicos(inicio_bloque_muestras, muestras_actuales)

            if slider_general.manejar_evento(evento):
                muestras_actuales = slider_general.val
                slider_fino.val_min = muestras_actuales - 500
                slider_fino.val_max = muestras_actuales + 500
                slider_fino.val = muestras_actuales
                slider_fino.actualizar_tirador_desde_val()
                audio.actualizar_parametros_dinamicos(inicio_bloque_muestras, muestras_actuales)
                
            if slider_fino.manejar_evento(evento):
                muestras_actuales = slider_fino.val
                slider_general.val = muestras_actuales
                slider_general.actualizar_tirador_desde_val()
                audio.actualizar_parametros_dinamicos(inicio_bloque_muestras, muestras_actuales)

            if slider_bloque.manejar_evento(evento):
                bloque_seleccionado = int(slider_bloque.val)
                inicio_bloque_muestras = offset_actual + (bloque_seleccionado - 1) * int(muestras_actuales)
                audio.actualizar_parametros_dinamicos(inicio_bloque_muestras, muestras_actuales)

            elif evento.type == pygame.KEYDOWN:
                paso_base = 0.1 if (pygame.key.get_mods() & pygame.KMOD_SHIFT) else 1.0

                if evento.key == pygame.K_RIGHT:
                    muestras_actuales += paso_base
                    slider_general.val = muestras_actuales
                    slider_general.actualizar_tirador_desde_val()
                    slider_fino.val = muestras_actuales
                    slider_fino.actualizar_tirador_desde_val()
                    audio.actualizar_parametros_dinamicos(inicio_bloque_muestras, muestras_actuales)
                elif evento.key == pygame.K_LEFT:
                    muestras_actuales -= paso_base
                    if muestras_actuales < 100: muestras_actuales = 100.0
                    slider_general.val = muestras_actuales
                    slider_general.actualizar_tirador_desde_val()
                    slider_fino.val = muestras_actuales
                    slider_fino.actualizar_tirador_desde_val()
                    audio.actualizar_parametros_dinamicos(inicio_bloque_muestras, muestras_actuales)
                
                elif evento.key == pygame.K_SPACE:
                    if audio.esta_reproduciendo():
                        audio.stop()
                    else:
                        bucle = True if (pygame.key.get_mods() & pygame.KMOD_SHIFT) else False
                        audio.play(inicio_bloque_muestras, muestras_actuales, loop=bucle)
                
                elif evento.key == pygame.K_RETURN:
                    stream.stop()
                    stream.close()
                    pygame.quit()
                    audio.exportar_loops(audio_seg, offset_actual, int(muestras_actuales), fps)
                    sys.exit()

        posicion_aguja = audio.obtener_puntero_global()

        # --- DIBUJADO ESTABLE ---
        pantalla.fill((20, 20, 25))
        ui.dibujar_onda_y_aguja(pantalla, audio_g, max_amplitud_global, inicio_bloque_muestras, muestras_actuales, posicion_aguja, ancho_w, alto_w)
        
        slider_offset.dibujar   (pantalla, fuente, fuente_lcd)
        slider_general.dibujar  (pantalla, fuente, fuente_lcd)
        slider_fino.dibujar     (pantalla, fuente, fuente_lcd)
        slider_bloque.dibujar   (pantalla, fuente, fuente_lcd)
        
        pygame.display.flip()

    stream.stop()
    stream.close()
    pygame.quit()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        ruta, fichero = filesys.obtener_nombre_fichero(tipos_archivo=[("WAVE", "*.wav"),("MP3", "*.mp3")])
        if ruta is None or fichero is None:
            print("Se necesita un parámetro: < ARCHIVO-AUDIO (wav o mp3) > [ intervalo ] [ offset ]")
            exit(1)
        main(fichero)
    else:        
        if len(sys.argv) < 3:
            main(sys.argv[1])
        elif len(sys.argv) < 4:
            main(sys.argv[1], sys.argv[2])                
        elif len(sys.argv) < 5:
            main(sys.argv[1], sys.argv[2], sys.argv[3])
                
