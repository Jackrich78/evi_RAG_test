--
-- PostgreSQL database dump
--

-- Dumped from database version 15.4 (Debian 15.4-2.pgdg120+1)
-- Dumped by pg_dump version 15.4 (Debian 15.4-2.pgdg120+1)

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
-- Name: pg_trgm; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;


--
-- Name: EXTENSION pg_trgm; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pg_trgm IS 'text similarity measurement and index searching based on trigrams';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';


--
-- Name: get_document_chunks(uuid); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.get_document_chunks(doc_id uuid) RETURNS TABLE(chunk_id uuid, content text, chunk_index integer, metadata jsonb)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        id AS chunk_id,
        chunks.content,
        chunks.chunk_index,
        chunks.metadata
    FROM chunks
    WHERE document_id = doc_id
    ORDER BY chunk_index;
END;
$$;


ALTER FUNCTION public.get_document_chunks(doc_id uuid) OWNER TO postgres;

--
-- Name: hybrid_search(public.vector, text, integer, double precision); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.hybrid_search(query_embedding public.vector, query_text text, match_count integer DEFAULT 10, text_weight double precision DEFAULT 0.3) RETURNS TABLE(chunk_id uuid, document_id uuid, content text, combined_score double precision, vector_similarity double precision, text_similarity double precision, metadata jsonb, document_title text, document_source text)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    WITH vector_results AS (
        SELECT
            c.id AS chunk_id,
            c.document_id,
            c.content,
            1 - (c.embedding <=> query_embedding) AS vector_sim,
            c.metadata,
            d.title AS doc_title,
            d.source AS doc_source
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE c.embedding IS NOT NULL
    ),
    text_results AS (
        SELECT
            c.id AS chunk_id,
            c.document_id,
            c.content,
            -- Updated to use Dutch language for full-text search
            ts_rank_cd(to_tsvector('dutch', c.content), plainto_tsquery('dutch', query_text)) AS text_sim,
            c.metadata,
            d.title AS doc_title,
            d.source AS doc_source
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        -- Updated to use Dutch language for full-text search
        WHERE to_tsvector('dutch', c.content) @@ plainto_tsquery('dutch', query_text)
    )
    SELECT
        COALESCE(v.chunk_id, t.chunk_id) AS chunk_id,
        COALESCE(v.document_id, t.document_id) AS document_id,
        COALESCE(v.content, t.content) AS content,
        CAST((COALESCE(v.vector_sim, 0) * (1 - text_weight) + COALESCE(t.text_sim, 0) * text_weight) AS DOUBLE PRECISION) AS combined_score,
        CAST(COALESCE(v.vector_sim, 0) AS DOUBLE PRECISION) AS vector_similarity,
        CAST(COALESCE(t.text_sim, 0) AS DOUBLE PRECISION) AS text_similarity,
        COALESCE(v.metadata, t.metadata) AS metadata,
        COALESCE(v.doc_title, t.doc_title) AS document_title,
        COALESCE(v.doc_source, t.doc_source) AS document_source
    FROM vector_results v
    FULL OUTER JOIN text_results t ON v.chunk_id = t.chunk_id
    ORDER BY combined_score DESC
    LIMIT match_count;
END;
$$;


ALTER FUNCTION public.hybrid_search(query_embedding public.vector, query_text text, match_count integer, text_weight double precision) OWNER TO postgres;

--
-- Name: match_chunks(public.vector, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.match_chunks(query_embedding public.vector, match_count integer DEFAULT 10) RETURNS TABLE(chunk_id uuid, document_id uuid, content text, similarity double precision, metadata jsonb, document_title text, document_source text)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id AS chunk_id,
        c.document_id,
        c.content,
        1 - (c.embedding <=> query_embedding) AS similarity,
        c.metadata,
        d.title AS document_title,
        d.source AS document_source
    FROM chunks c
    JOIN documents d ON c.document_id = d.id
    WHERE c.embedding IS NOT NULL
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;


ALTER FUNCTION public.match_chunks(query_embedding public.vector, match_count integer) OWNER TO postgres;

--
-- Name: search_guidelines_by_tier(public.vector, text, integer, integer, double precision); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.search_guidelines_by_tier(query_embedding public.vector, query_text text, tier_filter integer DEFAULT NULL::integer, match_count integer DEFAULT 10, text_weight double precision DEFAULT 0.3) RETURNS TABLE(chunk_id uuid, document_id uuid, content text, tier integer, combined_score double precision, vector_similarity double precision, text_similarity double precision, metadata jsonb, document_title text, document_source text)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    WITH vector_results AS (
        SELECT
            c.id AS chunk_id,
            c.document_id,
            c.content,
            c.tier,
            1 - (c.embedding <=> query_embedding) AS vector_sim,
            c.metadata,
            d.title AS doc_title,
            d.source AS doc_source
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE c.embedding IS NOT NULL
            AND (tier_filter IS NULL OR c.tier = tier_filter)
    ),
    text_results AS (
        SELECT
            c.id AS chunk_id,
            c.document_id,
            c.content,
            c.tier,
            ts_rank_cd(to_tsvector('dutch', c.content), plainto_tsquery('dutch', query_text)) AS text_sim,
            c.metadata,
            d.title AS doc_title,
            d.source AS doc_source
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE to_tsvector('dutch', c.content) @@ plainto_tsquery('dutch', query_text)
            AND (tier_filter IS NULL OR c.tier = tier_filter)
    )
    SELECT
        COALESCE(v.chunk_id, t.chunk_id) AS chunk_id,
        COALESCE(v.document_id, t.document_id) AS document_id,
        COALESCE(v.content, t.content) AS content,
        COALESCE(v.tier, t.tier) AS tier,
        CAST((COALESCE(v.vector_sim, 0) * (1 - text_weight) + COALESCE(t.text_sim, 0) * text_weight) AS DOUBLE PRECISION) AS combined_score,
        CAST(COALESCE(v.vector_sim, 0) AS DOUBLE PRECISION) AS vector_similarity,
        CAST(COALESCE(t.text_sim, 0) AS DOUBLE PRECISION) AS text_similarity,
        COALESCE(v.metadata, t.metadata) AS metadata,
        COALESCE(v.doc_title, t.doc_title) AS document_title,
        COALESCE(v.doc_source, t.doc_source) AS document_source
    FROM vector_results v
    FULL OUTER JOIN text_results t ON v.chunk_id = t.chunk_id
    ORDER BY
        -- Prioritize lower tiers (1=summary, 2=key facts) when no tier filter
        CASE WHEN tier_filter IS NULL THEN COALESCE(v.tier, t.tier) ELSE 0 END ASC,
        combined_score DESC
    LIMIT match_count;
END;
$$;


ALTER FUNCTION public.search_guidelines_by_tier(query_embedding public.vector, query_text text, tier_filter integer, match_count integer, text_weight double precision) OWNER TO postgres;

--
-- Name: FUNCTION search_guidelines_by_tier(query_embedding public.vector, query_text text, tier_filter integer, match_count integer, text_weight double precision); Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON FUNCTION public.search_guidelines_by_tier(query_embedding public.vector, query_text text, tier_filter integer, match_count integer, text_weight double precision) IS 'Tier-aware hybrid search for guidelines with Dutch language support';


--
-- Name: search_products(public.vector, text, text[], integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.search_products(query_embedding public.vector, query_text text, compliance_tags_filter text[] DEFAULT NULL::text[], match_count integer DEFAULT 10) RETURNS TABLE(product_id uuid, name text, description text, url text, category text, similarity double precision, compliance_tags text[], metadata jsonb)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id AS product_id,
        p.name,
        p.description,
        p.url,
        p.category,
        1 - (p.embedding <=> query_embedding) AS similarity,
        p.compliance_tags,
        p.metadata
    FROM products p
    WHERE p.embedding IS NOT NULL
        AND (compliance_tags_filter IS NULL OR p.compliance_tags && compliance_tags_filter)
    ORDER BY p.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;


ALTER FUNCTION public.search_products(query_embedding public.vector, query_text text, compliance_tags_filter text[], match_count integer) OWNER TO postgres;

--
-- Name: FUNCTION search_products(query_embedding public.vector, query_text text, compliance_tags_filter text[], match_count integer); Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON FUNCTION public.search_products(query_embedding public.vector, query_text text, compliance_tags_filter text[], match_count integer) IS 'Semantic search for products with compliance tag filtering';


--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_updated_at_column() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: chunks; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.chunks (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    document_id uuid NOT NULL,
    content text NOT NULL,
    embedding public.vector(1536),
    chunk_index integer NOT NULL,
    metadata jsonb DEFAULT '{}'::jsonb,
    token_count integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    tier integer,
    CONSTRAINT chunks_tier_check CHECK ((tier = ANY (ARRAY[1, 2, 3])))
);


ALTER TABLE public.chunks OWNER TO postgres;

--
-- Name: COLUMN chunks.tier; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.chunks.tier IS 'Guideline tier: 1=Summary, 2=Key Facts, 3=Detailed Content';


--
-- Name: documents; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.documents (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    title text NOT NULL,
    source text NOT NULL,
    content text NOT NULL,
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.documents OWNER TO postgres;

--
-- Name: document_summaries; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.document_summaries AS
 SELECT d.id,
    d.title,
    d.source,
    d.created_at,
    d.updated_at,
    d.metadata,
    count(c.id) AS chunk_count,
    avg(c.token_count) AS avg_tokens_per_chunk,
    sum(c.token_count) AS total_tokens
   FROM (public.documents d
     LEFT JOIN public.chunks c ON ((d.id = c.document_id)))
  GROUP BY d.id, d.title, d.source, d.created_at, d.updated_at, d.metadata;


ALTER TABLE public.document_summaries OWNER TO postgres;

--
-- Name: guideline_tier_stats; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.guideline_tier_stats AS
 SELECT chunks.tier,
    count(*) AS chunk_count,
    count(DISTINCT chunks.document_id) AS document_count,
    avg(chunks.token_count) AS avg_token_count,
    min(chunks.created_at) AS oldest_chunk,
    max(chunks.created_at) AS newest_chunk
   FROM public.chunks
  WHERE (chunks.tier IS NOT NULL)
  GROUP BY chunks.tier
  ORDER BY chunks.tier;


ALTER TABLE public.guideline_tier_stats OWNER TO postgres;

--
-- Name: messages; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.messages (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    session_id uuid NOT NULL,
    role text NOT NULL,
    content text NOT NULL,
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT messages_role_check CHECK ((role = ANY (ARRAY['user'::text, 'assistant'::text, 'system'::text])))
);


ALTER TABLE public.messages OWNER TO postgres;

--
-- Name: products; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.products (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    name text NOT NULL,
    description text NOT NULL,
    url text NOT NULL,
    category text,
    subcategory text,
    embedding public.vector(1536),
    compliance_tags text[] DEFAULT '{}'::text[],
    metadata jsonb DEFAULT '{}'::jsonb,
    source text DEFAULT 'evi360_website'::text,
    last_scraped_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.products OWNER TO postgres;

--
-- Name: TABLE products; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.products IS 'EVI 360 product catalog with embeddings for semantic search';


--
-- Name: COLUMN products.compliance_tags; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.products.compliance_tags IS 'Safety standards and compliance tags (e.g., EN_361, CE_certified)';


--
-- Name: product_catalog_summary; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.product_catalog_summary AS
 WITH unnested_tags AS (
         SELECT products.category,
            unnest(products.compliance_tags) AS tag,
            products.created_at,
            products.last_scraped_at,
            products.subcategory
           FROM public.products
          WHERE (products.category IS NOT NULL)
        )
 SELECT unnested_tags.category,
    count(*) AS product_count,
    count(DISTINCT unnested_tags.subcategory) AS subcategory_count,
    array_agg(DISTINCT unnested_tags.tag) AS all_compliance_tags,
    min(unnested_tags.created_at) AS oldest_product,
    max(unnested_tags.last_scraped_at) AS last_scrape
   FROM unnested_tags
  GROUP BY unnested_tags.category
  ORDER BY (count(*)) DESC;


ALTER TABLE public.product_catalog_summary OWNER TO postgres;

--
-- Name: sessions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sessions (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id text,
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    expires_at timestamp with time zone
);


ALTER TABLE public.sessions OWNER TO postgres;

--
-- Name: chunks chunks_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chunks
    ADD CONSTRAINT chunks_pkey PRIMARY KEY (id);


--
-- Name: documents documents_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_pkey PRIMARY KEY (id);


--
-- Name: messages messages_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_pkey PRIMARY KEY (id);


--
-- Name: products products_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (id);


--
-- Name: products products_url_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_url_key UNIQUE (url);


--
-- Name: sessions sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_pkey PRIMARY KEY (id);


--
-- Name: idx_chunks_chunk_index; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_chunks_chunk_index ON public.chunks USING btree (document_id, chunk_index);


--
-- Name: idx_chunks_content_trgm; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_chunks_content_trgm ON public.chunks USING gin (content public.gin_trgm_ops);


--
-- Name: idx_chunks_document_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_chunks_document_id ON public.chunks USING btree (document_id);


--
-- Name: idx_chunks_embedding; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_chunks_embedding ON public.chunks USING ivfflat (embedding public.vector_cosine_ops) WITH (lists='1');


--
-- Name: idx_chunks_tier; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_chunks_tier ON public.chunks USING btree (tier);


--
-- Name: idx_chunks_tier_document; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_chunks_tier_document ON public.chunks USING btree (tier, document_id);


--
-- Name: idx_documents_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_documents_created_at ON public.documents USING btree (created_at DESC);


--
-- Name: idx_documents_metadata; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_documents_metadata ON public.documents USING gin (metadata);


--
-- Name: idx_messages_session_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_messages_session_id ON public.messages USING btree (session_id, created_at);


--
-- Name: idx_products_category; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_products_category ON public.products USING btree (category);


--
-- Name: idx_products_compliance_tags; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_products_compliance_tags ON public.products USING gin (compliance_tags);


--
-- Name: idx_products_embedding; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_products_embedding ON public.products USING ivfflat (embedding public.vector_cosine_ops) WITH (lists='1');


--
-- Name: idx_products_metadata; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_products_metadata ON public.products USING gin (metadata);


--
-- Name: idx_products_url; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_products_url ON public.products USING btree (url);


--
-- Name: idx_sessions_expires_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_sessions_expires_at ON public.sessions USING btree (expires_at);


--
-- Name: idx_sessions_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_sessions_user_id ON public.sessions USING btree (user_id);


--
-- Name: documents update_documents_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON public.documents FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: products update_products_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON public.products FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: sessions update_sessions_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON public.sessions FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: chunks chunks_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chunks
    ADD CONSTRAINT chunks_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE;


--
-- Name: messages messages_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.sessions(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

