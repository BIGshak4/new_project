-- ============================================================================
-- 1100  Structural seed
-- Source: src/MVP_Build_Guide.md §3.3 (launch subjects), src/Data_Models.md §5.1 (Generic)
--
-- Only structure that the code depends on. The leaf skill catalog, the
-- Digital Hardware Engineer role and its skill set are JSON seed files under
-- backend/seeds/ and loaded by backend/scripts/seed_db.py, so they can be
-- reviewed by a practitioner before use.
-- ============================================================================

-- The six launch subjects (domain nodes) for the Digital Hardware track.
insert into public.skill (key, label, description, node_type, family, category)
values
  ('digital_fundamentals', 'Digital Fundamentals',
   'Number systems, Boolean algebra, logic gates, combinational building blocks (mux, decoder, adder), simplification, timing basics.',
   'domain', 'hardware', 'technical'),
  ('sequential_logic', 'Sequential Logic',
   'Latches and flip-flops, registers, counters, shift registers, synchronous vs asynchronous reset, setup and hold, clock domains.',
   'domain', 'hardware', 'technical'),
  ('fsms', 'FSMs',
   'Moore and Mealy machines, state encoding, sequence detectors, state minimization, FSM coding style in HDL, common FSM bugs.',
   'domain', 'hardware', 'technical'),
  ('relevant_programming', 'Relevant Programming',
   'HDL basics (Verilog or SystemVerilog), blocking vs non-blocking, testbench structure, plus Python or C as used in hardware workflows.',
   'domain', 'hardware', 'technical'),
  ('reasoning', 'Reasoning',
   'Problem decomposition, estimation, trade-off reasoning, risk and failure-mode awareness, debugging methodology.',
   'domain', 'general', 'problem_solving'),
  ('projects_behavioral', 'Projects & Behavioral',
   'Explaining a project end to end, ownership, teamwork, learning from mistakes, structured communication.',
   'domain', 'general', 'culture');

-- The Generic company: no company skill set, weight share 0, so a generic
-- session uses the role skill set alone (Data_Models §5.1).
insert into public.company_profile
  (slug, display_name, industry, core_values, risk_tolerance, interview_style,
   company_weight_share, culture_prompt_block, is_public, version)
values
  ('generic', 'Generic', null, '[]'::jsonb, 5,
   '{"pacing": "measured", "follow_up_aggressiveness": 0.5, "ambiguity_injection": 0.2, "tone": "neutral_and_encouraging"}'::jsonb,
   0.00, '', true, 1);
