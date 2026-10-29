---
autor: [Nombre]
fecha: [AAAA-MM-DD]
titulo: [Nombre de la Funcionalidad]
estado: [Estado de la Funcionalidad]
---

# TDD-[XXXX]: [Nombre de la Funcionalidad]

## Contexto de Negocio (PRD)

### Objetivo
[Descripción del valor de negocio y qué problema resuelve.]

### User Persona
*   **Nombre**: [Nombre del rol/persona]
*   **Necesidad**: [Descripción de lo que necesita lograr y sus puntos de dolor.]

### Criterios de Aceptación
*   [Criterio 1: ej. El sistema debe validar que...]
*   [Criterio 2: ej. Al finalizar, el sistema debe...]
*   [Criterio 3: ej. El estado por defecto debe ser...]

## Diseño Técnico (RFC)

### Modelo de Datos
[Descripción de las entidades, sus propiedades y restricciones.]
*   `campo`: Tipo (Restricciones).

### Contrato de API
[Definición de endpoints y contratos de entrada/salida.]
*   **Endpoint**: `METHOD /api/v1/[recurso]`
*   **Request Body**:
```ts
{
    // propiedades
}
```

### Estructura del Código
[Cómo se organiza la implementación y sus responsabilidades.]
*   **Capa X**: [Responsabilidad y ejemplos de lo que contiene]
*   **Capa Y**: [Responsabilidad y ejemplos de lo que contiene]
*   **Capa Z**: [Responsabilidad y ejemplos de lo que contiene]

## Casos de Borde y Errores
| Escenario                   | Resultado Esperado                            | Código HTTP               |
| ----------------------------| --------------------------------------------- | ------------------------- |
| [Ej: DNI ya registrado]     | [Error de validación con mensaje claro]       | 409 Conflict              |
| [Ej: Formato email inválido]| [Error de validación de formato]              | 400 Bad Request           |

## Plan de Implementación
1. [Paso 1: ej. Definir el modelo de datos y sus restricciones]
2. [Paso 2: ej. Implementar la validación de reglas de negocio]
3. [Paso 3: ej. Exponer el endpoint y conectar con la capa de persistencia]
4. [Paso 4: ej. Agregar tests unitarios y de integración]