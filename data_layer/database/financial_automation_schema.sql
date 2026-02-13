--
-- PostgreSQL database dump
--

-- Dumped from database version 14.18 (Homebrew)
-- Dumped by pg_dump version 14.18 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: workflowstatus; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.workflowstatus AS ENUM (
    'PLANNED',
    'EXECUTING',
    'COMPLETED',
    'FAILED',
    'CANCELLED'
);


ALTER TYPE public.workflowstatus OWNER TO postgres;

--
-- Name: workflowtype; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.workflowtype AS ENUM (
    'DOCUMENT_EXTRACTION',
    'REPORT_GENERATION'
);


ALTER TYPE public.workflowtype OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: companies; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.companies (
    id character varying(36) NOT NULL,
    name character varying(255) NOT NULL,
    tax_id character varying(50),
    registration_number character varying(50),
    email character varying(255),
    phone character varying(50),
    website character varying(255),
    address_line1 character varying(255),
    address_line2 character varying(255),
    city character varying(100),
    state character varying(100),
    country character varying(100),
    postal_code character varying(20),
    logo_url character varying(500),
    primary_color character varying(7) DEFAULT '#1976D2'::character varying,
    secondary_color character varying(7) DEFAULT '#424242'::character varying,
    currency character varying(3) DEFAULT 'INR'::character varying,
    fiscal_year_start character varying(5),
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    company_aliases text[],
    dso_days integer DEFAULT 30
);


ALTER TABLE public.companies OWNER TO postgres;

--
-- Name: customer_invoices; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.customer_invoices (
    id character varying(36) NOT NULL,
    company_id character varying(36) NOT NULL,
    customer_id character varying(36),
    document_id character varying(36),
    invoice_number character varying(100) NOT NULL,
    invoice_date timestamp without time zone,
    due_date timestamp without time zone,
    subtotal_amount numeric(15,2),
    tax_amount numeric(15,2),
    total_amount numeric(15,2),
    received_amount numeric(15,2) DEFAULT 0.0,
    outstanding_amount numeric(15,2),
    original_currency character varying(3),
    exchange_rate numeric(10,6),
    inr_amount numeric(15,2),
    payment_status character varying(20) DEFAULT 'unpaid'::character varying,
    payment_terms_days integer,
    line_items jsonb,
    notes text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.customer_invoices OWNER TO postgres;

--
-- Name: customers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.customers (
    id character varying(36) NOT NULL,
    company_id character varying(36) NOT NULL,
    customer_name character varying(255) NOT NULL,
    customer_code character varying(50),
    tax_id character varying(50),
    email character varying(255),
    phone character varying(50),
    website character varying(255),
    address_line1 character varying(255),
    address_line2 character varying(255),
    city character varying(100),
    state character varying(100),
    country character varying(100),
    postal_code character varying(20),
    payment_terms_days integer DEFAULT 30,
    credit_limit numeric(15,2),
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.customers OWNER TO postgres;

--
-- Name: documents; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.documents (
    id character varying(36) NOT NULL,
    company_id character varying(36) NOT NULL,
    file_name character varying(255) NOT NULL,
    file_path character varying(500),
    file_type character varying(10),
    file_size integer,
    document_type character varying(50),
    document_number character varying(100),
    document_date date,
    category character varying(50),
    docling_parsed_data jsonb,
    canonical_data jsonb,
    status character varying(50) DEFAULT 'pending'::character varying,
    confidence_score numeric(3,2),
    vendor_name character varying(255),
    customer_name character varying(255),
    grand_total numeric(15,2) DEFAULT 0.0,
    tax_total numeric(15,2) DEFAULT 0.0,
    paid_amount numeric(15,2) DEFAULT 0.0,
    outstanding numeric(15,2) DEFAULT 0.0,
    uploaded_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    parsed_at timestamp without time zone,
    processed_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.documents OWNER TO postgres;

--
-- Name: user_settings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_settings (
    id integer NOT NULL,
    user_id text NOT NULL,
    company_name text NOT NULL,
    company_legal_name text,
    tax_id text,
    address_line1 text,
    address_line2 text,
    city text,
    state text,
    country text,
    postal_code text,
    email text,
    phone text,
    website text,
    logo_path text,
    primary_color text DEFAULT '#1a73e8'::text,
    secondary_color text DEFAULT '#34a853'::text,
    accent_color text DEFAULT '#fbbc04'::text,
    default_currency text DEFAULT 'INR'::text,
    date_format text DEFAULT 'MM/DD/YYYY'::text,
    sla_days integer DEFAULT 30,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.user_settings OWNER TO postgres;

--
-- Name: user_settings_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.user_settings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_settings_id_seq OWNER TO postgres;

--
-- Name: user_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.user_settings_id_seq OWNED BY public.user_settings.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id character varying(36) NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    full_name character varying(255),
    company_id character varying(36) NOT NULL,
    is_active boolean,
    created_at timestamp without time zone,
    last_login timestamp without time zone
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: vendor_invoices; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.vendor_invoices (
    id character varying(36) NOT NULL,
    company_id character varying(36) NOT NULL,
    vendor_id character varying(36),
    document_id character varying(36),
    invoice_number character varying(100) NOT NULL,
    invoice_date date,
    due_date date,
    subtotal_amount numeric(15,2),
    tax_amount numeric(15,2),
    total_amount numeric(15,2),
    paid_amount numeric(15,2) DEFAULT 0.0,
    outstanding_amount numeric(15,2),
    original_currency character varying(3),
    exchange_rate numeric(10,6),
    inr_amount numeric(15,2),
    payment_status character varying(20) DEFAULT 'unpaid'::character varying,
    payment_terms_days integer,
    line_items jsonb,
    notes text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.vendor_invoices OWNER TO postgres;

--
-- Name: vendors; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.vendors (
    id character varying(36) NOT NULL,
    company_id character varying(36) NOT NULL,
    vendor_name character varying(255) NOT NULL,
    vendor_code character varying(50),
    tax_id character varying(50),
    email character varying(255),
    phone character varying(50),
    website character varying(255),
    address_line1 character varying(255),
    address_line2 character varying(255),
    city character varying(100),
    state character varying(100),
    country character varying(100),
    postal_code character varying(20),
    payment_terms_days integer DEFAULT 30,
    credit_limit numeric(15,2),
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.vendors OWNER TO postgres;

--
-- Name: workflow_execution_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.workflow_execution_logs (
    id character varying(36) NOT NULL,
    workflow_id character varying(36) NOT NULL,
    step_number integer NOT NULL,
    step_id character varying(50) NOT NULL,
    node_type character varying(100) NOT NULL,
    status character varying(20),
    input_data jsonb,
    output_data jsonb,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    execution_time_ms integer,
    error_message text,
    stack_trace text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.workflow_execution_logs OWNER TO postgres;

--
-- Name: workflow_nodes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.workflow_nodes (
    id character varying(36) NOT NULL,
    workflow_id character varying(36) NOT NULL,
    node_id character varying(50) NOT NULL,
    node_type character varying(100) NOT NULL,
    node_name character varying(255),
    position_x integer,
    position_y integer,
    params json,
    input_data json,
    output_data json,
    status character varying(20),
    execution_time_ms integer,
    error_message text,
    "order" integer,
    created_at timestamp without time zone
);


ALTER TABLE public.workflow_nodes OWNER TO postgres;

--
-- Name: workflows; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.workflows (
    id character varying(36) NOT NULL,
    name character varying(255) NOT NULL,
    type character varying(50) NOT NULL,
    status character varying(50) DEFAULT 'planned'::character varying NOT NULL,
    company_id character varying(50) NOT NULL,
    user_id character varying(50) NOT NULL,
    query text,
    domain character varying(50),
    report_type character varying(100),
    workflow_definition jsonb NOT NULL,
    execution_result jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    output_file_path character varying(500),
    execution_time_ms integer,
    error_message text
);


ALTER TABLE public.workflows OWNER TO postgres;

--
-- Name: user_settings id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_settings ALTER COLUMN id SET DEFAULT nextval('public.user_settings_id_seq'::regclass);


--
-- Name: companies companies_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.companies
    ADD CONSTRAINT companies_pkey PRIMARY KEY (id);


--
-- Name: customer_invoices customer_invoices_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.customer_invoices
    ADD CONSTRAINT customer_invoices_pkey PRIMARY KEY (id);


--
-- Name: customers customers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_pkey PRIMARY KEY (id);


--
-- Name: documents documents_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_pkey PRIMARY KEY (id);


--
-- Name: user_settings user_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_settings
    ADD CONSTRAINT user_settings_pkey PRIMARY KEY (id);


--
-- Name: user_settings user_settings_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_settings
    ADD CONSTRAINT user_settings_user_id_key UNIQUE (user_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: vendor_invoices vendor_invoices_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vendor_invoices
    ADD CONSTRAINT vendor_invoices_pkey PRIMARY KEY (id);


--
-- Name: vendors vendors_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vendors
    ADD CONSTRAINT vendors_pkey PRIMARY KEY (id);


--
-- Name: workflow_execution_logs workflow_execution_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workflow_execution_logs
    ADD CONSTRAINT workflow_execution_logs_pkey PRIMARY KEY (id);


--
-- Name: workflow_nodes workflow_nodes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workflow_nodes
    ADD CONSTRAINT workflow_nodes_pkey PRIMARY KEY (id);


--
-- Name: workflows workflows_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workflows
    ADD CONSTRAINT workflows_pkey PRIMARY KEY (id);


--
-- Name: idx_companies_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_companies_name ON public.companies USING btree (name);


--
-- Name: idx_customer_invoices_company; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_customer_invoices_company ON public.customer_invoices USING btree (company_id);


--
-- Name: idx_customer_invoices_customer; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_customer_invoices_customer ON public.customer_invoices USING btree (customer_id);


--
-- Name: idx_customer_invoices_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_customer_invoices_date ON public.customer_invoices USING btree (invoice_date);


--
-- Name: idx_customer_invoices_due; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_customer_invoices_due ON public.customer_invoices USING btree (due_date);


--
-- Name: idx_customer_invoices_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_customer_invoices_status ON public.customer_invoices USING btree (payment_status);


--
-- Name: idx_customers_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_customers_active ON public.customers USING btree (is_active);


--
-- Name: idx_customers_company; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_customers_company ON public.customers USING btree (company_id);


--
-- Name: idx_customers_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_customers_name ON public.customers USING btree (customer_name);


--
-- Name: idx_documents_category; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_documents_category ON public.documents USING btree (category);


--
-- Name: idx_documents_company; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_documents_company ON public.documents USING btree (company_id);


--
-- Name: idx_documents_number; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_documents_number ON public.documents USING btree (document_number);


--
-- Name: idx_documents_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_documents_type ON public.documents USING btree (document_type);


--
-- Name: idx_documents_uploaded; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_documents_uploaded ON public.documents USING btree (uploaded_at);


--
-- Name: idx_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_user_id ON public.user_settings USING btree (user_id);


--
-- Name: idx_vendor_invoices_company; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_vendor_invoices_company ON public.vendor_invoices USING btree (company_id);


--
-- Name: idx_vendor_invoices_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_vendor_invoices_date ON public.vendor_invoices USING btree (invoice_date);


--
-- Name: idx_vendor_invoices_due; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_vendor_invoices_due ON public.vendor_invoices USING btree (due_date);


--
-- Name: idx_vendor_invoices_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_vendor_invoices_status ON public.vendor_invoices USING btree (payment_status);


--
-- Name: idx_vendor_invoices_vendor; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_vendor_invoices_vendor ON public.vendor_invoices USING btree (vendor_id);


--
-- Name: idx_vendors_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_vendors_active ON public.vendors USING btree (is_active);


--
-- Name: idx_vendors_company; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_vendors_company ON public.vendors USING btree (company_id);


--
-- Name: idx_vendors_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_vendors_name ON public.vendors USING btree (vendor_name);


--
-- Name: idx_workflow_logs_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_workflow_logs_created ON public.workflow_execution_logs USING btree (created_at);


--
-- Name: idx_workflow_logs_workflow; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_workflow_logs_workflow ON public.workflow_execution_logs USING btree (workflow_id);


--
-- Name: idx_workflows_company; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_workflows_company ON public.workflows USING btree (company_id);


--
-- Name: idx_workflows_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_workflows_created ON public.workflows USING btree (created_at);


--
-- Name: idx_workflows_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_workflows_status ON public.workflows USING btree (status);


--
-- Name: idx_workflows_user; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_workflows_user ON public.workflows USING btree (user_id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_workflow_nodes_workflow_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_workflow_nodes_workflow_id ON public.workflow_nodes USING btree (workflow_id);


--
-- Name: customer_invoices customer_invoices_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.customer_invoices
    ADD CONSTRAINT customer_invoices_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: customer_invoices customer_invoices_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.customer_invoices
    ADD CONSTRAINT customer_invoices_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(id);


--
-- Name: customer_invoices customer_invoices_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.customer_invoices
    ADD CONSTRAINT customer_invoices_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id);


--
-- Name: customers customers_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: documents documents_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: vendor_invoices vendor_invoices_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vendor_invoices
    ADD CONSTRAINT vendor_invoices_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: vendor_invoices vendor_invoices_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vendor_invoices
    ADD CONSTRAINT vendor_invoices_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id);


--
-- Name: vendor_invoices vendor_invoices_vendor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vendor_invoices
    ADD CONSTRAINT vendor_invoices_vendor_id_fkey FOREIGN KEY (vendor_id) REFERENCES public.vendors(id);


--
-- Name: vendors vendors_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vendors
    ADD CONSTRAINT vendors_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- PostgreSQL database dump complete
--

