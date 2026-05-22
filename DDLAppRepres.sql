-- ============================================================
-- DDL — Sistema de Notificaciones
-- Representantes Estudiantiles | Proyecto Final BI 2026-I
-- ============================================================

DROP TABLE CASOS_ELECTORAL  CASCADE CONSTRAINTS PURGE;
DROP TABLE NOTIFICACIONES   CASCADE CONSTRAINTS PURGE;
DROP TABLE EVENTOS          CASCADE CONSTRAINTS PURGE;
DROP TABLE REPRESENTANTES   CASCADE CONSTRAINTS PURGE;

-- ──────────────────────────────────────────────
-- 1. REPRESENTANTES
-- ──────────────────────────────────────────────
CREATE TABLE REPRESENTANTES (
    representante_id  NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    numero_documento  VARCHAR2(20)  NOT NULL,
    nombre            VARCHAR2(100) NOT NULL,
    estamento         VARCHAR2(60)  NOT NULL,
    estado            VARCHAR2(10)  DEFAULT 'Activo' NOT NULL,

    CONSTRAINT chk_estado_rep
        CHECK (estado IN ('Activo', 'Inactivo')),
    CONSTRAINT uq_documento_rep
        UNIQUE (numero_documento)
);

-- ──────────────────────────────────────────────
-- 2. EVENTOS
-- ──────────────────────────────────────────────
CREATE TABLE EVENTOS (
    evento_id   NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre      VARCHAR2(100) NOT NULL,
    tipo        VARCHAR2(20)  NOT NULL,
    fecha       DATE,

    CONSTRAINT chk_tipo_evento
        CHECK (tipo IN ('Asamblea', 'Evento')),
    CONSTRAINT uq_nombre_evento
        UNIQUE (nombre)
);

-- ──────────────────────────────────────────────
-- 3. NOTIFICACIONES
-- ──────────────────────────────────────────────
CREATE TABLE NOTIFICACIONES (
    notificacion_id   NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    representante_id  NUMBER        NOT NULL,
    evento_id         NUMBER        NOT NULL,
    fecha_registro    DATE          DEFAULT SYSDATE NOT NULL,
    motivo            VARCHAR2(200) DEFAULT 'Inasistencia registrada' NOT NULL,
    estado            VARCHAR2(15)  DEFAULT 'Vigente' NOT NULL,

    CONSTRAINT fk_noti_representante
        FOREIGN KEY (representante_id)
        REFERENCES REPRESENTANTES(representante_id),
    CONSTRAINT fk_noti_evento
        FOREIGN KEY (evento_id)
        REFERENCES EVENTOS(evento_id),
    CONSTRAINT uq_rep_evento
        UNIQUE (representante_id, evento_id),
    CONSTRAINT chk_estado_noti
        CHECK (estado IN ('Vigente', 'Apelada', 'Anulada'))
);

-- ──────────────────────────────────────────────
-- 4. CASOS_ELECTORAL
-- ──────────────────────────────────────────────
CREATE TABLE CASOS_ELECTORAL (
    caso_id            NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    representante_id   NUMBER        NOT NULL,
    fecha_envio        DATE          DEFAULT SYSDATE NOT NULL,
    num_notificaciones NUMBER        NOT NULL,
    estado             VARCHAR2(25)  DEFAULT 'Pendiente de envio' NOT NULL,
    observaciones      VARCHAR2(300),

    CONSTRAINT fk_caso_representante
        FOREIGN KEY (representante_id)
        REFERENCES REPRESENTANTES(representante_id),
    CONSTRAINT uq_caso_por_rep
        UNIQUE (representante_id),
    CONSTRAINT chk_num_notificaciones
        CHECK (num_notificaciones >= 3),
    CONSTRAINT chk_estado_caso
        CHECK (estado IN ('Pendiente de envio', 'Enviado al Electoral',
                          'No se considera', 'Archivado'))
);