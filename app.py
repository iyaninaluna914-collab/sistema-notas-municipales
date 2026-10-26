
import streamlit as st
import mysql.connector
from datetime import date

st.set_page_config(
    page_title="Sistema Municipal de Notas",
    page_icon="📄",
    layout="wide"
)


# CONEXIÓN A LA BASE DE DATOS
def conectar():
    return mysql.connector.connect(
        host=st.secrets["mysql"]["host"],
        port=int(st.secrets["mysql"]["port"]),
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"]
    )


st.title("📄 Sistema Municipal de Registro de Notas")
st.write("Registro, clasificación y seguimiento de notas municipales.")

# MENÚ PRINCIPAL
opcion = st.sidebar.selectbox(
    "Menú principal",
    [
        "Inicio",
        "Registrar nota",
        "Buscar notas",
        "Seguimiento de notas",
        "Historial de notas"
    ]
)

st.sidebar.divider()
st.sidebar.caption("Sistema Municipal")


try:
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    # ==========================================
    # INICIO
    # ==========================================
    if opcion == "Inicio":
        st.header("Bienvenido al sistema")
        st.write(
            "Desde este sistema se podrán registrar, "
            "clasificar y consultar las notas municipales."
        )

        cursor.execute("SELECT COUNT(*) AS total FROM notas")
        total = cursor.fetchone()["total"]

        st.metric("Total de notas registradas", total)

        st.info(
            "Seleccioná una opción del menú de la izquierda "
            "para comenzar."
        )

    # ==========================================
    # REGISTRAR NOTA
    # ==========================================
    elif opcion == "Registrar nota":
        st.header("Registrar una nueva nota")

        cursor.execute("""
            SELECT id_area, nombre_area
            FROM areas
            ORDER BY nombre_area
        """)
        areas = cursor.fetchall()

        if not areas:
            st.warning("No hay áreas registradas.")
        else:
            nombres_areas = {
                area["nombre_area"]: area["id_area"]
                for area in areas
            }

            with st.form("formulario_nota"):
                numero_ingreso = st.text_input(
                    "Número de ingreso",
                    placeholder="Ejemplo: NOTA-0008"
                )

                fecha_ingreso = st.date_input(
                    "Fecha de ingreso",
                    value=date.today()
                )

                remitente = st.text_input("Nombre del remitente")
                asunto = st.text_input("Asunto")
                descripcion = st.text_area("Descripción")

                area_seleccionada = st.selectbox(
                    "Área responsable",
                    list(nombres_areas.keys())
                )

                guardar = st.form_submit_button("Guardar nota")

            if guardar:
                if not numero_ingreso.strip():
                    st.error("Ingresá el número de ingreso.")
                elif not remitente.strip():
                    st.error("Ingresá el nombre del remitente.")
                elif not asunto.strip():
                    st.error("Ingresá el asunto.")
                elif not descripcion.strip():
                    st.error("Ingresá una descripción.")
                else:
                    try:
                        cursor.execute("""
                            INSERT INTO notas (
                                numero_ingreso,
                                fecha_ingreso,
                                remitente,
                                asunto,
                                descripcion,
                                id_area_actual,
                                estado_actual
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (
                            numero_ingreso.strip(),
                            fecha_ingreso,
                            remitente.strip(),
                            asunto.strip(),
                            descripcion.strip(),
                            nombres_areas[area_seleccionada],
                            "Recibida"
                        ))

                        conexion.commit()
                        st.success("¡Nota registrada correctamente!")
                        st.rerun()

                    except mysql.connector.Error as error:
                        conexion.rollback()

                        if error.errno == 1062:
                            st.error(
                                "Ese número de ingreso ya existe. "
                                "Ingresá otro número."
                            )
                        else:
                            st.error("No se pudo guardar la nota.")
                            st.write("Detalle:", str(error))

    # ==========================================
    # BUSCAR NOTAS
    # ==========================================
    elif opcion == "Buscar notas":
        st.header("Consultar notas registradas")

        busqueda = st.text_input(
            "Buscar por número, remitente o asunto",
            placeholder="Escribí una palabra o número"
        )

        termino = "%" + busqueda.strip() + "%"

        cursor.execute("""
            SELECT
                n.numero_ingreso,
                n.fecha_ingreso,
                n.remitente,
                n.asunto,
                n.descripcion,
                a.nombre_area AS area_responsable,
                n.estado_actual
            FROM notas n
            JOIN areas a ON n.id_area_actual = a.id_area
            WHERE n.numero_ingreso LIKE %s
               OR n.remitente LIKE %s
               OR n.asunto LIKE %s
            ORDER BY n.id_nota DESC
        """, (termino, termino, termino))

        notas = cursor.fetchall()

        if notas:
            st.caption(f"Resultados encontrados: {len(notas)}")
            st.dataframe(
                notas,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No se encontraron notas.")

    # ==========================================
    # SEGUIMIENTO DE NOTAS
    # ==========================================
    elif opcion == "Seguimiento de notas":
        st.header("Seguimiento y derivación de notas")

        # Consultar notas existentes
        cursor.execute("""
            SELECT
                n.id_nota,
                n.numero_ingreso,
                n.remitente,
                n.asunto,
                n.id_area_actual,
                n.estado_actual,
                a.nombre_area AS area_actual
            FROM notas n
            JOIN areas a ON n.id_area_actual = a.id_area
            ORDER BY n.id_nota DESC
        """)
        notas_disponibles = cursor.fetchall()

        # Consultar áreas
        cursor.execute("""
            SELECT id_area, nombre_area
            FROM areas
            ORDER BY nombre_area
        """)
        areas = cursor.fetchall()

        if not notas_disponibles:
            st.info("Todavía no hay notas para realizar el seguimiento.")

        elif not areas:
            st.warning("No hay áreas registradas.")

        else:
            # Preparar las opciones para elegir una nota
            opciones_notas = {
                (
                    f'{n["numero_ingreso"]} - '
                    f'{n["asunto"]} '
                    f'({n["estado_actual"]})'
                ): n
                for n in notas_disponibles
            }

            nota_elegida = st.selectbox(
                "Seleccioná la nota",
                list(opciones_notas.keys())
            )

            nota = opciones_notas[nota_elegida]

            st.subheader("Información actual de la nota")
            st.write("**Número:**", nota["numero_ingreso"])
            st.write("**Remitente:**", nota["remitente"])
            st.write("**Asunto:**", nota["asunto"])
            st.write("**Área actual:**", nota["area_actual"])
            st.write("**Estado actual:**", nota["estado_actual"])

            nombres_areas = {
                area["nombre_area"]: area["id_area"]
                for area in areas
            }

            area_actual = nota["area_actual"]
            nombres_disponibles = list(nombres_areas.keys())
            indice_area = (
                nombres_disponibles.index(area_actual)
                if area_actual in nombres_disponibles else 0
            )

            estados = [
                "Recibida",
                "Derivada",
                "En trámite",
                "Resuelta"
            ]

            estado_actual = nota["estado_actual"]
            indice_estado = (
                estados.index(estado_actual)
                if estado_actual in estados else 0
            )

            st.divider()
            st.subheader("Registrar movimiento")

            with st.form("formulario_seguimiento"):
                area_destino = st.selectbox(
                    "Área responsable",
                    nombres_disponibles,
                    index=indice_area
                )

                nuevo_estado = st.selectbox(
                    "Nuevo estado",
                    estados,
                    index=indice_estado
                )

                usuario_responsable = st.text_input(
                    "Nombre de quien realiza el movimiento"
                )

                observacion = st.text_area(
                    "Observación",
                    placeholder=(
                        "Ejemplo: Se deriva la solicitud para "
                        "revisar y reparar las luminarias."
                    )
                )

                guardar_movimiento = st.form_submit_button(
                    "Guardar seguimiento"
                )

            if guardar_movimiento:
                if not usuario_responsable.strip():
                    st.error(
                        "Ingresá el nombre de quien realiza el movimiento."
                    )

                elif not observacion.strip():
                    st.error("Ingresá una observación.")

                else:
                    try:
                        id_area_destino = nombres_areas[area_destino]

                        # Describir también los cambios de área
                        detalle_observacion = observacion.strip()

                        if area_destino != nota["area_actual"]:
                            detalle_observacion = (
                                f'Área anterior: {nota["area_actual"]}. '
                                f'Área nueva: {area_destino}. '
                                f'{detalle_observacion}'
                            )

                        # Actualizar área y estado de la nota
                        cursor.execute("""
                            UPDATE notas
                            SET id_area_actual = %s,
                                estado_actual = %s
                            WHERE id_nota = %s
                        """, (
                            id_area_destino,
                            nuevo_estado,
                            nota["id_nota"]
                        ))

                        # Guardar el movimiento en el historial
                        cursor.execute("""
                            INSERT INTO historial_seguimiento (
                                id_nota,
                                usuario_responsable,
                                estado_anterior,
                                estado_nuevo,
                                observacion,
                                fecha_hora
                            )
                            VALUES (%s, %s, %s, %s, %s, NOW())
                        """, (
                            nota["id_nota"],
                            usuario_responsable.strip(),
                            nota["estado_actual"],
                            nuevo_estado,
                            detalle_observacion
                        ))

                        conexion.commit()
                        st.success(
                            "¡Seguimiento guardado correctamente!"
                        )
                        st.rerun()

                    except mysql.connector.Error as error:
                        conexion.rollback()
                        st.error("No se pudo guardar el seguimiento.")
                        st.write("Detalle:", str(error))

            # Mostrar historial de movimientos
            st.divider()
            st.subheader("Historial de esta nota")

            cursor.execute("""
                SELECT
                    usuario_responsable,
                    estado_anterior,
                    estado_nuevo,
                    observacion,
                    fecha_hora
                FROM historial_seguimiento
                WHERE id_nota = %s
                ORDER BY fecha_hora DESC, id_seguimiento DESC
            """, (nota["id_nota"],))

            historial = cursor.fetchall()

            if historial:
                st.dataframe(
                    historial,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info(
                    "Esta nota todavía no tiene movimientos "
                    "registrados en el historial."
                )
                
    # ==========================================
    # HISTORIAL DE NOTAS
    # ==========================================
    elif opcion == "Historial de notas":
        st.header("📋 Historial completo de notas")
        st.write(
            "Consultá todos los movimientos registrados "
            "de una nota municipal."
        )

        cursor.execute("""
            SELECT
                n.id_nota,
                n.numero_ingreso,
                n.remitente,
                n.asunto,
                n.estado_actual,
                a.nombre_area AS area_actual
            FROM notas n
            JOIN areas a ON n.id_area_actual = a.id_area
            ORDER BY n.id_nota DESC
        """)

        notas_historial = cursor.fetchall()

        if not notas_historial:
            st.info("Todavía no hay notas registradas.")

        else:
            opciones_historial = {
                (
                    f'{n["numero_ingreso"]} - '
                    f'{n["asunto"]}'
                ): n
                for n in notas_historial
            }

            nota_seleccionada = st.selectbox(
                "Seleccioná la nota que querés consultar",
                list(opciones_historial.keys()),
                key="nota_historial"
            )

            nota_historial = opciones_historial[nota_seleccionada]

            st.subheader("Información de la nota")
            st.write("**Número:**", nota_historial["numero_ingreso"])
            st.write("**Remitente:**", nota_historial["remitente"])
            st.write("**Asunto:**", nota_historial["asunto"])
            st.write("**Área actual:**", nota_historial["area_actual"])
            st.write("**Estado actual:**", nota_historial["estado_actual"])

            st.divider()
            st.subheader("Movimientos registrados")

            cursor.execute("""
                SELECT
                    usuario_responsable AS 'Responsable',
                    estado_anterior AS 'Estado anterior',
                    estado_nuevo AS 'Estado nuevo',
                    observacion AS 'Observación',
                    fecha_hora AS 'Fecha y hora'
                FROM historial_seguimiento
                WHERE id_nota = %s
                ORDER BY fecha_hora DESC, id_seguimiento DESC
            """, (nota_historial["id_nota"],))

            movimientos = cursor.fetchall()

            if movimientos:
                st.dataframe(
                    movimientos,
                    use_container_width=True,
                    hide_index=True
                )
                st.success(
                    f"Se encontraron {len(movimientos)} movimientos."
                )
            else:
                st.info(
                    "Esta nota todavía no tiene movimientos "
                    "registrados en el historial."
                )


    cursor.close()
    conexion.close()

except Exception as error:
    st.error("Ocurrió un problema con la aplicación o la base de datos.")
    st.write("Detalle del error:", str(error))
