import streamlit as st
import pandas as pd
from conection import get_connection

st.set_page_config(
    page_title="Gestión Humana",
    page_icon="📋",
    layout="wide"
)

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
defaults = {
    "vista": "landing",
    "rep_cedula": None,
    "umbral": 3,
    "periodo": "2025-2 / 2026-1",
    "clave_admin": "gestion2025",
    "form_nuevo_evento": False,
    "editar_evento": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

UMBRAL = st.session_state.umbral

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def query(sql, params=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, params or {})
    cols = [c[0] for c in cur.description]
    return pd.DataFrame(cur.fetchall(), columns=cols)

def dml(sql, params=None):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(sql, params or {})
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False

def badge(n):
    if n == 0:
        return "🟢 Sin notificaciones"
    elif n < UMBRAL:
        return f"🟡 {n} notificación{'es' if n > 1 else ''}"
    else:
        return f"🔴 {n} notificaciones"

def color_fila(row):
    n = row["Notificaciones"]
    if n >= UMBRAL:
        return ["background-color: #7f1d1d; color: #fecaca"] * len(row)
    elif n == UMBRAL - 1:
        return ["background-color: #78350f; color: #fef3c7"] * len(row)
    return [""] * len(row)

# ═════════════════════════════════════════════
# LANDING
# ═════════════════════════════════════════════
if st.session_state.vista == "landing":
    st.markdown(f"### 📋 Gestión Humana &nbsp;&nbsp; `{st.session_state.periodo}`")
    st.divider()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## Consulta tus notificaciones")
        cedula = st.text_input("Número de documento", placeholder="Ej: 1027801574")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔍 Consultar", use_container_width=True, type="primary"):
                if not cedula.strip():
                    st.warning("Ingresa tu número de documento.")
                else:
                    rep = query(
                        "SELECT representante_id FROM REPRESENTANTES WHERE numero_documento = :c",
                        {"c": cedula.strip()}
                    )
                    if rep.empty:
                        st.error("No se encontró ningún representante con ese documento.")
                    else:
                        st.session_state.rep_cedula = cedula.strip()
                        st.session_state.vista = "rep"
                        st.rerun()
        with c2:
            if st.button("🔐 Coordinador", use_container_width=True):
                st.session_state.vista = "login"
                st.rerun()

# ═════════════════════════════════════════════
# LOGIN
# ═════════════════════════════════════════════
elif st.session_state.vista == "login":
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## 🔐 Acceso Coordinador")
        clave = st.text_input("Contraseña", type="password")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Entrar", use_container_width=True, type="primary"):
                if clave == st.session_state.clave_admin:
                    st.session_state.vista = "admin"
                    st.rerun()
                else:
                    st.error("Contraseña incorrecta.")
        with c2:
            if st.button("← Volver", use_container_width=True):
                st.session_state.vista = "landing"
                st.rerun()

# ═════════════════════════════════════════════
# VISTA REPRESENTANTE
# ═════════════════════════════════════════════
elif st.session_state.vista == "rep":
    cedula = st.session_state.rep_cedula
    rep = query(
        "SELECT representante_id, nombre, estamento FROM REPRESENTANTES WHERE numero_documento = :c",
        {"c": cedula}
    )
    nombre    = rep["NOMBRE"].iloc[0]
    estamento = rep["ESTAMENTO"].iloc[0]
    rep_id    = int(rep["REPRESENTANTE_ID"].iloc[0])

    notis = query("""
        SELECT e.nombre AS "Evento", e.tipo AS "Tipo",
               TO_CHAR(e.fecha, 'DD/MM/YYYY') AS "Fecha",
               n.estado AS "Estado"
        FROM NOTIFICACIONES n
        JOIN EVENTOS e ON e.evento_id = n.evento_id
        WHERE n.representante_id = :rid
        ORDER BY n.fecha_registro
    """, {"rid": rep_id})

    total = len(notis[notis["Estado"] == "Vigente"]) if not notis.empty else 0
    caso  = query(
        "SELECT estado FROM CASOS_ELECTORAL WHERE representante_id = :rid",
        {"rid": rep_id}
    )

    st.markdown(f"### 📋 Gestión Humana &nbsp;&nbsp; `{st.session_state.periodo}`")
    st.divider()
    st.markdown(f"## Hola, {nombre.split()[0]} 👋")
    st.caption(estamento)
    st.markdown(f"### {badge(total)}")
    st.markdown("")

    if total >= UMBRAL:
        st.error("⚠️ Acumulaste 3 o más notificaciones. Tu caso puede ser enviado al Comité Electoral.")
    elif total == UMBRAL - 1:
        st.warning("Estás a una notificación de ser enviado al Comité Electoral.")
    else:
        st.success("Vas bien. Sigue asistiendo a las asambleas y eventos.")

    if not caso.empty:
        mapa = {
            "Enviado al Electoral": "🔴 Tu caso fue enviado al Comité Electoral.",
            "Pendiente de envio":   "🟡 Tu caso está pendiente de envío al Comité Electoral.",
            "No se considera":      "⚪ Tu caso no se considera para sanción.",
            "Archivado":            "⚫ Tu caso fue archivado.",
        }
        st.info(mapa.get(caso["ESTADO"].iloc[0], caso["ESTADO"].iloc[0]))

    st.divider()
    st.subheader("📋 Mis notificaciones")
    if notis.empty:
        st.success("No tienes ninguna notificación registrada.")
    else:
        st.dataframe(notis, use_container_width=True, hide_index=True)

    if st.button("← Volver"):
        st.session_state.vista = "landing"
        st.session_state.rep_cedula = None
        st.rerun()

# ═════════════════════════════════════════════
# ADMIN
# ═════════════════════════════════════════════
elif st.session_state.vista == "admin":

    col_h1, col_h2 = st.columns([5, 1])
    with col_h1:
        st.markdown(f"### 📋 Gestión Humana &nbsp;&nbsp; `{st.session_state.periodo}` &nbsp; 🟢 En línea")
    with col_h2:
        if st.button("🚪 Cerrar sesión", use_container_width=True):
            st.session_state.vista = "landing"
            st.rerun()

    tab_panel, tab_reps, tab_eventos, tab_electoral, tab_config = st.tabs([
        "📊 Panel", "👥 Representantes", "📅 Eventos", "⚖️ Electoral", "⚙️ Config."
    ])

    # ── PANEL ─────────────────────────────────────────────────────────────
    with tab_panel:
        stats = query("""
                SELECT
                    -- 1. Total Representantes
                    (SELECT COUNT(*) FROM REPRESENTANTES WHERE estado = 'Activo') AS total_reps,

                    -- 2. Sin incumplimientos (Cero notificaciones vigentes)
                    (SELECT COUNT(*) FROM REPRESENTANTES r
                     WHERE r.estado = 'Activo'
                       AND NOT EXISTS (
                           SELECT 1 FROM NOTIFICACIONES n
                           WHERE n.representante_id = r.representante_id AND n.estado = 'Vigente'
                       )
                    ) AS sin_incumplimientos,

                    -- 3. Con 1-2 notificaciones (Alerta)
                    (SELECT COUNT(*) FROM (
                        SELECT r.representante_id
                        FROM REPRESENTANTES r
                        JOIN NOTIFICACIONES n ON n.representante_id = r.representante_id
                        WHERE r.estado = 'Activo' AND n.estado = 'Vigente'
                        GROUP BY r.representante_id
                        HAVING COUNT(n.notificacion_id) > 0 AND COUNT(n.notificacion_id) < :u
                    )) AS en_alerta,

                    -- 4. Con 3+ notificaciones (Requieren acción)
                    (SELECT COUNT(*) FROM (
                        SELECT r.representante_id
                        FROM REPRESENTANTES r
                        JOIN NOTIFICACIONES n ON n.representante_id = r.representante_id
                        WHERE r.estado = 'Activo' AND n.estado = 'Vigente'
                        GROUP BY r.representante_id
                        HAVING COUNT(n.notificacion_id) >= :u
                    )) AS con_tres_mas,

                    -- 5. Pendientes de enviar (Tienen 3+ pero aún no tienen caso creado)
                    (SELECT COUNT(*) FROM (
                        SELECT r.representante_id
                        FROM REPRESENTANTES r
                        JOIN NOTIFICACIONES n ON n.representante_id = r.representante_id
                        WHERE r.estado = 'Activo' AND n.estado = 'Vigente'
                        AND NOT EXISTS (
                            SELECT 1 FROM CASOS_ELECTORAL c
                            WHERE c.representante_id = r.representante_id
                        )
                        GROUP BY r.representante_id
                        HAVING COUNT(n.notificacion_id) >= :u
                    )) AS pendientes
                FROM DUAL
            """, {"u": UMBRAL})

        # Ahora creamos 5 columnas en lugar de 4
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("👥 Total Representantes", int(stats["TOTAL_REPS"].iloc[0]), "Período activo")
        c2.metric("✅ Sin incumplimientos", int(stats["SIN_INCUMPLIMIENTOS"].iloc[0]), "Estado óptimo")
        c3.metric("🟡 Con 1-2 notificaciones", int(stats["EN_ALERTA"].iloc[0]), "Zona de alerta")
        c4.metric("🔴 Con 3+ notificaciones", int(stats["CON_TRES_MAS"].iloc[0]), "Requieren acción")
        c5.metric("⚖️ Pendientes de enviar", int(stats["PENDIENTES"].iloc[0]), "Al comité electoral")

        st.divider()
        col1, col2 = st.columns(2)

        with col1:
            total_3_mas = int(stats["CON_TRES_MAS"].iloc[0])
            st.subheader(f"⚠️ Con 3+ notificaciones ({total_3_mas})")

            top = query("""
                SELECT r.nombre AS "Representante", 
                       r.estamento AS "Estamento",
                       COUNT(n.notificacion_id) AS "Notificaciones",
                       NVL(c.estado, 'Pendiente de envio') AS "Estado Caso"
                FROM REPRESENTANTES r
                JOIN NOTIFICACIONES n ON n.representante_id = r.representante_id 
                                     AND n.estado = 'Vigente'
                LEFT JOIN CASOS_ELECTORAL c ON c.representante_id = r.representante_id
                WHERE r.estado = 'Activo'
                GROUP BY r.representante_id, r.nombre, r.estamento, c.estado
                HAVING COUNT(n.notificacion_id) >= :u
                ORDER BY "Notificaciones" DESC, r.nombre
            """, {"u": UMBRAL})

            st.dataframe(top, use_container_width=True, hide_index=True)

        with col2:
            st.subheader("📅 Eventos con más incumplimientos")
            top_ev = query("""
                SELECT e.nombre AS "Evento", e.tipo AS "Tipo",
                       COUNT(n.notificacion_id) AS "Incumplimientos"
                FROM EVENTOS e
                LEFT JOIN NOTIFICACIONES n ON n.evento_id = e.evento_id
                GROUP BY e.evento_id, e.nombre, e.tipo
                ORDER BY "Incumplimientos" DESC
                FETCH FIRST 5 ROWS ONLY
            """)
            st.dataframe(top_ev, use_container_width=True, hide_index=True)

    # ── REPRESENTANTES ────────────────────────────────────────────────────
    with tab_reps:
        busqueda = st.text_input("🔍 Buscar", placeholder="Nombre o documento...")

        where = "AND (UPPER(r.nombre) LIKE UPPER(:b) OR r.numero_documento LIKE :b)" if busqueda else ""
        params = {}  # Inicializamos vacío en lugar de pasar "u"
        if busqueda:
            params["b"] = f"%{busqueda}%"

        reps_df = query(f"""
                    SELECT r.representante_id,
                           r.numero_documento AS "Documento",
                           r.nombre           AS "Nombre",
                           r.estamento        AS "Estamento",
                           COUNT(n.notificacion_id) AS "Notificaciones"
                    FROM REPRESENTANTES r
                    LEFT JOIN NOTIFICACIONES n ON n.representante_id = r.representante_id
                                              AND n.estado = 'Vigente'
                    WHERE r.estado = 'Activo' {where}
                    GROUP BY r.representante_id, r.numero_documento, r.nombre, r.estamento
                    ORDER BY "Notificaciones" DESC, r.nombre
                """, params)

        st.caption(f"{len(reps_df)} representantes")
        display_df = reps_df.drop(columns=["REPRESENTANTE_ID"])
        st.dataframe(
            display_df.style.apply(color_fila, axis=1),
            use_container_width=True, hide_index=True
        )

        st.divider()
        st.subheader("➕ Registrar notificación")

        rep_map = dict(zip(
            reps_df["Nombre"] + " (" + reps_df["Documento"] + ")",
            reps_df["REPRESENTANTE_ID"]
        ))
        eventos_df = query("""
            SELECT evento_id,
                   nombre || CASE WHEN fecha IS NOT NULL
                             THEN ' — ' || TO_CHAR(fecha,'DD/MM/YYYY')
                             ELSE '' END AS desc_evento
            FROM EVENTOS ORDER BY fecha NULLS LAST
        """)
        evento_map = dict(zip(eventos_df["DESC_EVENTO"], eventos_df["EVENTO_ID"]))

        c1, c2 = st.columns(2)
        with c1:
            rep_sel = st.selectbox("Representante", list(rep_map.keys()), key="rep_noti")
        with c2:
            ev_sel  = st.selectbox("Evento", list(evento_map.keys()), key="ev_noti")
        motivo = st.text_input("Motivo", value="Inasistencia registrada")

        if st.button("✅ Registrar", type="primary"):
            rid = int(rep_map[rep_sel])
            eid = int(evento_map[ev_sel])
            existe = query("""
                SELECT 1 FROM NOTIFICACIONES
                WHERE representante_id = :r AND evento_id = :e
            """, {"r": rid, "e": eid})
            if not existe.empty:
                st.warning("Ese representante ya tiene notificación en ese evento.")
            else:
                if dml("""
                    INSERT INTO NOTIFICACIONES (representante_id, evento_id, motivo)
                    VALUES (:r, :e, :m)
                """, {"r": rid, "e": eid, "m": motivo}):
                    st.success("✅ Notificación registrada.")
                    st.rerun()

        st.divider()
        st.subheader("❌ Anular notificación")

        notis_vigentes = query("""
            SELECT n.notificacion_id,
                   r.nombre || ' — ' || e.nombre AS descripcion
            FROM NOTIFICACIONES n
            JOIN REPRESENTANTES r ON r.representante_id = n.representante_id
            JOIN EVENTOS e ON e.evento_id = n.evento_id
            WHERE n.estado = 'Vigente'
            ORDER BY r.nombre
        """)

        if notis_vigentes.empty:
            st.info("No hay notificaciones vigentes para anular.")
        else:
            noti_map = dict(zip(
                notis_vigentes["DESCRIPCION"],
                notis_vigentes["NOTIFICACION_ID"]
            ))
            sel_noti = st.selectbox("Notificación a anular", list(noti_map.keys()))
            if st.button("❌ Anular"):
                if dml("UPDATE NOTIFICACIONES SET estado='Anulada' WHERE notificacion_id=:n",
                       {"n": int(noti_map[sel_noti])}):
                    st.success("✅ Notificación anulada.")
                    st.rerun()

    # ── EVENTOS ───────────────────────────────────────────────────────────
    with tab_eventos:
        col_ev1, col_ev2 = st.columns([4, 1])
        with col_ev1:
            st.subheader("📅 Gestión de Eventos")
        with col_ev2:
            if st.button("+ Nuevo evento", type="primary", use_container_width=True):
                st.session_state.form_nuevo_evento = not st.session_state.form_nuevo_evento
                st.session_state.editar_evento = None

        if st.session_state.form_nuevo_evento:
            with st.form("form_nuevo_ev"):
                st.markdown("**Nuevo evento**")
                c1, c2, c3 = st.columns(3)
                with c1:
                    nom_ev  = st.text_input("Nombre")
                with c2:
                    tipo_ev = st.selectbox("Tipo", ["Asamblea", "Evento"])
                with c3:
                    fecha_ev = st.date_input("Fecha (opcional)", value=None)
                cs, cc = st.columns(2)
                with cs:
                    sub = st.form_submit_button("✅ Crear", type="primary")
                with cc:
                    can = st.form_submit_button("Cancelar")
                if sub:
                    if not nom_ev.strip():
                        st.error("El nombre es obligatorio.")
                    else:
                        existe_ev = query("SELECT 1 FROM EVENTOS WHERE nombre = :n", {"n": nom_ev.strip()})
                        if not existe_ev.empty:
                            st.error("Ya existe un evento con ese nombre.")
                        else:
                            if dml("INSERT INTO EVENTOS (nombre, tipo, fecha) VALUES (:n, :t, :f)",
                                   {"n": nom_ev.strip(), "t": tipo_ev, "f": fecha_ev or None}):
                                st.success("✅ Evento creado.")
                                st.session_state.form_nuevo_evento = False
                                st.rerun()
                if can:
                    st.session_state.form_nuevo_evento = False
                    st.rerun()

        eventos_lista = query("""
            SELECT e.evento_id, e.nombre, e.tipo,
                   TO_CHAR(e.fecha, 'YYYY-MM-DD') AS fecha,
                   COUNT(n.notificacion_id) AS incumplimientos
            FROM EVENTOS e
            LEFT JOIN NOTIFICACIONES n ON n.evento_id = e.evento_id
            GROUP BY e.evento_id, e.nombre, e.tipo, e.fecha
            ORDER BY e.fecha NULLS LAST, e.nombre
        """)

        st.caption(f"{len(eventos_lista)} eventos en el período")

        for _, ev in eventos_lista.iterrows():
            ev_id  = int(ev["EVENTO_ID"])
            ev_nom = ev["NOMBRE"]
            ev_tip = ev["TIPO"]
            ev_fec = ev["FECHA"] or "Sin fecha"
            ev_inc = int(ev["INCUMPLIMIENTOS"])
            badge_tipo = "🔵 Asamblea" if ev_tip == "Asamblea" else "🟠 Evento especial"
            inc_txt = f"{ev_inc} incumplimiento{'s' if ev_inc != 1 else ''} registrado{'s' if ev_inc != 1 else ''}"

            c1, c2, c3 = st.columns([5, 1, 1])
            with c1:
                st.markdown(f"**{ev_nom}** &nbsp; {badge_tipo}")
                st.caption(f"{ev_fec} · {inc_txt}")
            with c2:
                if st.button("Editar", key=f"edit_{ev_id}"):
                    st.session_state.editar_evento = ev_id if st.session_state.editar_evento != ev_id else None
                    st.session_state.form_nuevo_evento = False
            with c3:
                if st.button("Eliminar", key=f"del_{ev_id}"):
                    if ev_inc > 0:
                        st.error(f"No se puede eliminar: tiene {ev_inc} notificaciones.")
                    else:
                        if dml("DELETE FROM EVENTOS WHERE evento_id = :id", {"id": ev_id}):
                            st.success("Eliminado.")
                            st.rerun()

            if st.session_state.editar_evento == ev_id:
                with st.form(f"edit_{ev_id}"):
                    ca, cb = st.columns(2)
                    with ca:
                        nuevo_nom = st.text_input("Nombre", value=ev_nom)
                    with cb:
                        nuevo_tip = st.selectbox("Tipo", ["Asamblea", "Evento"],
                                                 index=0 if ev_tip == "Asamblea" else 1)
                    cg, cc2 = st.columns(2)
                    with cg:
                        guardar = st.form_submit_button("💾 Guardar")
                    with cc2:
                        cancelar = st.form_submit_button("Cancelar")
                    if guardar:
                        if dml("UPDATE EVENTOS SET nombre=:n, tipo=:t WHERE evento_id=:id",
                               {"n": nuevo_nom, "t": nuevo_tip, "id": ev_id}):
                            st.success("✅ Actualizado.")
                            st.session_state.editar_evento = None
                            st.rerun()
                    if cancelar:
                        st.session_state.editar_evento = None
                        st.rerun()

            st.divider()

    # ── ELECTORAL ─────────────────────────────────────────────────────────
    with tab_electoral:
        st.subheader("⚖️ Comité Electoral")

        casos = query("""
            SELECT c.caso_id, r.nombre, r.estamento,
                   c.num_notificaciones, c.estado,
                   TO_CHAR(c.fecha_envio, 'DD/MM/YYYY') AS fecha_envio,
                   c.observaciones
            FROM CASOS_ELECTORAL c
            JOIN REPRESENTANTES r ON r.representante_id = c.representante_id
            ORDER BY c.fecha_envio DESC
        """)

        estados_opciones = ["Pendiente de envio", "Enviado al Electoral", "No se considera", "Archivado"]

        if casos.empty:
            st.info("No hay casos registrados.")
        else:
            for _, caso in casos.iterrows():
                caso_id = int(caso["CASO_ID"])
                c1, c2, c3 = st.columns([3, 2, 1])
                with c1:
                    st.markdown(f"**{caso['NOMBRE']}**")
                    st.caption(f"{caso['ESTAMENTO']} · {int(caso['NUM_NOTIFICACIONES'])} notificaciones · {caso['FECHA_ENVIO']}")
                    if caso["OBSERVACIONES"]:
                        st.caption(f"📝 {caso['OBSERVACIONES']}")
                with c2:
                    idx = estados_opciones.index(caso["ESTADO"]) if caso["ESTADO"] in estados_opciones else 0
                    nuevo_estado = st.selectbox("Estado", estados_opciones, index=idx, key=f"est_{caso_id}")
                with c3:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("💾 Guardar", key=f"save_{caso_id}"):
                        if dml("UPDATE CASOS_ELECTORAL SET estado=:e WHERE caso_id=:id",
                               {"e": nuevo_estado, "id": caso_id}):
                            st.success("✅ Actualizado.")
                            st.rerun()
                st.divider()

        st.subheader("➕ Enviar nuevo caso")
        candidatos = query("""
            SELECT r.representante_id,
                   r.nombre || ' (' || COUNT(n.notificacion_id) || ' notif.)' AS desc_rep,
                   COUNT(n.notificacion_id) AS total
            FROM REPRESENTANTES r
            JOIN NOTIFICACIONES n ON n.representante_id = r.representante_id
                                  AND n.estado = 'Vigente'
            WHERE NOT EXISTS (
                SELECT 1 FROM CASOS_ELECTORAL c WHERE c.representante_id = r.representante_id
            )
            GROUP BY r.representante_id, r.nombre
            HAVING COUNT(n.notificacion_id) >= :u
            ORDER BY total DESC
        """, {"u": UMBRAL})

        if candidatos.empty:
            st.info("No hay representantes con 3+ notificaciones sin caso abierto.")
        else:
            cand_map  = dict(zip(candidatos["DESC_REP"],         candidatos["REPRESENTANTE_ID"]))
            total_map = dict(zip(candidatos["REPRESENTANTE_ID"], candidatos["TOTAL"]))
            c1, c2 = st.columns(2)
            with c1:
                cand_sel = st.selectbox("Representante", list(cand_map.keys()))
            with c2:
                est_sel = st.selectbox("Estado inicial", ["Pendiente de envio", "Enviado al Electoral"])
            obs = st.text_area("Observaciones (opcional)")
            if st.button("⚖️ Crear caso", type="primary"):
                rid   = int(cand_map[cand_sel])
                total = int(total_map[rid])
                if dml("""
                    INSERT INTO CASOS_ELECTORAL
                           (representante_id, num_notificaciones, estado, observaciones)
                    VALUES (:r, :t, :e, :o)
                """, {"r": rid, "t": total, "e": est_sel, "o": obs or None}):
                    st.success("✅ Caso creado.")
                    st.rerun()

    # ── CONFIG ────────────────────────────────────────────────────────────
    with tab_config:
        st.subheader("⚙️ Configuración")
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("**Período académico**")
            nuevo_periodo = st.text_input("Período", value=st.session_state.periodo)
            if st.button("💾 Guardar período"):
                st.session_state.periodo = nuevo_periodo
                st.success("✅ Período actualizado.")
                st.rerun()

            st.divider()
            st.markdown("**Umbral de notificaciones**")
            st.caption("Número de notificaciones a partir del cual se activa el proceso electoral.")
            nuevo_umbral = st.number_input("Umbral", min_value=1, max_value=10,
                                           value=st.session_state.umbral)
            if st.button("💾 Guardar umbral"):
                st.session_state.umbral = int(nuevo_umbral)
                st.success(f"✅ Umbral actualizado a {int(nuevo_umbral)}.")
                st.rerun()

        with c2:
            st.markdown("**Cambiar contraseña**")
            clave_actual = st.text_input("Contraseña actual", type="password", key="ca")
            clave_nueva  = st.text_input("Nueva contraseña",  type="password", key="cn")
            clave_conf   = st.text_input("Confirmar nueva",   type="password", key="cc")
            if st.button("🔐 Cambiar contraseña"):
                if clave_actual != st.session_state.clave_admin:
                    st.error("La contraseña actual es incorrecta.")
                elif not clave_nueva:
                    st.error("La nueva contraseña no puede estar vacía.")
                elif clave_nueva != clave_conf:
                    st.error("Las contraseñas no coinciden.")
                else:
                    st.session_state.clave_admin = clave_nueva
                    st.success("✅ Contraseña actualizada.")