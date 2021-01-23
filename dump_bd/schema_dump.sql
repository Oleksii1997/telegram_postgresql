--
-- PostgreSQL database dump
--

-- Dumped from database version 13.1 (Ubuntu 13.1-1.pgdg18.04+1)
-- Dumped by pg_dump version 13.1 (Ubuntu 13.1-1.pgdg18.04+1)

-- Started on 2021-01-22 23:56:26 EET

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 202 (class 1259 OID 16891)
-- Name: city; Type: TABLE; Schema: public; Owner: Oleksii
--

CREATE TABLE public.city (
    id_city integer NOT NULL,
    district integer,
    city_name character varying(255) NOT NULL,
    city_url character varying(700) NOT NULL
);


ALTER TABLE public.city OWNER TO "Oleksii";

--
-- TOC entry 201 (class 1259 OID 16877)
-- Name: district; Type: TABLE; Schema: public; Owner: Oleksii
--

CREATE TABLE public.district (
    id_district integer NOT NULL,
    region integer,
    district_name character varying(255) NOT NULL,
    district_url character varying(700) NOT NULL
);


ALTER TABLE public.district OWNER TO "Oleksii";

--
-- TOC entry 200 (class 1259 OID 16861)
-- Name: region; Type: TABLE; Schema: public; Owner: Oleksii
--

CREATE TABLE public.region (
    id integer NOT NULL,
    region_name character varying(255) NOT NULL,
    region_url character varying(700)
);


ALTER TABLE public.region OWNER TO "Oleksii";

--
-- TOC entry 2845 (class 2606 OID 16898)
-- Name: city city_pkey; Type: CONSTRAINT; Schema: public; Owner: Oleksii
--

ALTER TABLE ONLY public.city
    ADD CONSTRAINT city_pkey PRIMARY KEY (id_city);


--
-- TOC entry 2843 (class 2606 OID 16884)
-- Name: district district_pkey; Type: CONSTRAINT; Schema: public; Owner: Oleksii
--

ALTER TABLE ONLY public.district
    ADD CONSTRAINT district_pkey PRIMARY KEY (id_district);


--
-- TOC entry 2841 (class 2606 OID 16868)
-- Name: region region_pkey; Type: CONSTRAINT; Schema: public; Owner: Oleksii
--

ALTER TABLE ONLY public.region
    ADD CONSTRAINT region_pkey PRIMARY KEY (id);


--
-- TOC entry 2847 (class 2606 OID 16899)
-- Name: city city_district_fkey; Type: FK CONSTRAINT; Schema: public; Owner: Oleksii
--

ALTER TABLE ONLY public.city
    ADD CONSTRAINT city_district_fkey FOREIGN KEY (district) REFERENCES public.district(id_district);


--
-- TOC entry 2846 (class 2606 OID 16885)
-- Name: district district_region_fkey; Type: FK CONSTRAINT; Schema: public; Owner: Oleksii
--

ALTER TABLE ONLY public.district
    ADD CONSTRAINT district_region_fkey FOREIGN KEY (region) REFERENCES public.region(id);


-- Completed on 2021-01-22 23:56:26 EET

--
-- PostgreSQL database dump complete
--

