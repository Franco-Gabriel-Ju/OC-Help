# Proyecto Compliador OC

Es un sistema que espero que ayude con la matera Organizacion Computacional

## 📌 Descripción
Este proyecto tiene como objetivo desarrollar un programa que permita enteder 
Mejor como se organiza una computadora
Está pensado para los estudiantes.  
Tecnologías: Python, PLY.


## Estructura
¡Perfecto! 🚀
Con la estructura que armás en tu script, lo que tenés es una **arquitectura típica de proyecto educativo modular**. Te detallo qué debería ir en cada carpeta (ejemplo para un proyecto en **JavaScript/TypeScript o similar**, pero podés adaptarlo a tu stack):

---

### 📂 **docs/**

* Documentación del proyecto (manuales de uso, guías de instalación, diagramas, requerimientos).
* Puede incluir un `README.md` más detallado, PDF con especificaciones, etc.

---

### 📂 **config/**

* Archivos de configuración generales.
* Ejemplo:

  * `webpack.config.js` / `vite.config.js`
  * `eslint.json`
  * `tsconfig.json`
  * Config de entorno (`.env.example`).

---

### 📂 **src/**

Código fuente principal de la aplicación. Dentro de esta:

#### 📂 **assets/**

* Recursos estáticos: imágenes, íconos, fuentes, audios, estilos CSS/SCSS.

#### 📂 **components/**

* Componentes reutilizables de UI (botones, formularios, menús, layouts).
* Cada componente debería estar desacoplado y fácil de reutilizar.

#### 📂 **modules/**

Organización por materias o áreas temáticas.

* **matematicas/**

  * 📂 `lecciones/` → Contenido teórico (texto, presentaciones, material base).
  * 📂 `ejercicios/` → Archivos de práctica interactiva, problemas a resolver.
  * 📂 `evaluaciones/` → Quizzes, tests o evaluaciones automatizadas.

* **historia/**

  * Contenido estructurado de la materia Historia (puede seguir la misma lógica: lecciones, actividades, evaluaciones).

#### 📂 **services/**

* Lógica para interactuar con APIs o bases de datos.
* Ejemplo: `userService.js`, `authService.js`, `quizService.js`.

#### 📂 **store/**

* Manejo del **estado global** (si usás Redux, Zustand, Vuex, Pinia, etc.).
* Ejemplo: `store.js` o módulos de estado separados.

#### 📂 **utils/**

* Funciones auxiliares / helpers.
* Ejemplo: formateo de fechas, validación de datos, cálculos comunes.

#### 📂 **app/**

* Punto de entrada principal de la aplicación.
* Aquí vivirá `App.jsx` / `App.tsx` o la estructura raíz de la app.

---

### 📂 **tests/**

* Pruebas unitarias e integrales.
* Ejemplo:

  * `matematicas.test.js`
  * `historia.test.js`
  * Carpetas paralelas a `modules/` para testear cada parte.

---

### 📂 **scripts/**

* Scripts auxiliares (como el `crear_estructura.ps1`).
* Otros ejemplos:

  * Scripts de despliegue.
  * Migraciones de base de datos.
  * Automatizaciones de limpieza o instalación.

---

👉 Con esta organización, tu proyecto queda **modular, escalable y mantenible**.

¿Querés que te arme un **README.md** inicial donde se explique esta estructura carpeta por carpeta, listo para poner en tu repo?
