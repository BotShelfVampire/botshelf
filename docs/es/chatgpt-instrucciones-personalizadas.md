# Instrucciones personalizadas de ChatGPT: plantilla práctica

Las Instrucciones personalizadas sirven para preferencias estables que repetirías en muchas conversaciones: tu función, audiencia, tono, formato de salida y límites. La tarea concreta y los datos actuales deben ir en el mensaje de cada conversación.

Rutas actuales indicadas por OpenAI:

- Web y escritorio: **Configuración → Personalización → Instrucciones personalizadas**
- iOS y Android: **Configuración → Personalizar ChatGPT**

Fuente oficial: [ChatGPT Custom Instructions](https://help.openai.com/en/articles/8096356-custom-instructions-for-chatgpt)

## Plantilla para copiar y pegar

Sustituye los corchetes y elimina lo que no necesites.

```text
Mi función y contexto:
- Trabajo como [función] en [sector].
- Mi audiencia habitual es [audiencia].
- Da por hecho que conozco [temas], pero explica [temas] con claridad.

Estilo de respuesta:
- Empieza por la respuesta.
- Sé breve salvo que pida más profundidad.
- Usa prosa clara. Emplea listas o tablas solo cuando ayuden.
- Conserva exactamente los números, nombres, enlaces y restricciones que proporcione.
- En los borradores, entrega texto listo para copiar sin comentarios adicionales.

Evidencia e incertidumbre:
- No inventes hechos, citas, fuentes, pruebas, usuarios ni métricas.
- Separa los hechos confirmados de las suposiciones.
- Si la actualidad importa, verifica la información o indica qué no puede comprobarse.
- Si la confianza es limitada, indícala como alta, media o baja.

Acciones y seguridad:
- Toma decisiones rutinarias y reversibles sin preguntar.
- Pregunta antes de gastar, enviar, publicar, borrar o cambiar accesos.
- No expongas credenciales ni datos privados.
```

## Cómo mantenerla útil

1. Úsala para valores predeterminados, no para un informe completo de proyecto.
2. Conserva solo las reglas que mejoren varios tipos de conversación.
3. Pruébala con tres tareas normales.
4. Si las respuestas se vuelven rígidas o repetitivas, elimina reglas solapadas antes de añadir más.
5. Indica las excepciones en el mensaje de la tarea, por ejemplo: «Para esta respuesta, explica con detalle».

No guardes contraseñas, claves de API, claves de monedero, registros de clientes ni información personal sensible en las Instrucciones personalizadas.

## Nota de verificación

Esta plantilla no demuestra que un modelo concreto vaya a seguir todas las reglas. Pruébala con tu cuenta, modelo y tareas, y conserva la entrada y la salida reales antes de afirmar resultados.

BotShelf Vampire es independiente de OpenAI.
