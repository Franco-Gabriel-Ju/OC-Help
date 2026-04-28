# Calculadora OC Web (Flask)

## Ejecutar

1. Instalar dependencias:

```powershell
c:/Users/Alexxe/Documents/OC-Help/proyect-OC/.venv/Scripts/python.exe -m pip install -r calculadora/web/requirements.txt
```

2. Levantar servidor:

```powershell
c:/Users/Alexxe/Documents/OC-Help/proyect-OC/.venv/Scripts/python.exe calculadora/web/app.py
```

3. Abrir en navegador:

`http://127.0.0.1:5000`

## Endpoints

- `POST /api/convert`
- `POST /api/convert-all` (equivalente a la vista principal: DEC/BIN/HEX/OCT)
- `POST /api/nc2nc`
- `POST /api/nc2cs` (salida en formato de clase: signo 0/1)
- `POST /api/suma-nc`
- `POST /api/manual` (pasos didacticos del conversor)

## Vistas incluidas

- Calculadora
- NC -> NC
- NC -> CS (signo 0/1)
- Suma NC
- Resolucion Manual
