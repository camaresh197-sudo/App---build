# FINDINGS BANK v2
# Shared by BOTH agents (Wren and Greg) — user rule 2026-11-23: write on the spot
# after every noteworthy discovery, in your own domain, signed with your name+version.
# schema: id|date|domain|facts(key:val,comma-sep)|note|source
# rules: append new = next id (S%03d, highest+1). Refine same subject = edit
# that record in place, bump date, append fact keys. NEVER delete a record;
# superseded = status field value 'superseded_by:Sxxx'. One line, no wrapping.
# domains: singer|piper|voice|song|process|tool|game|model
S001|2026-11-23|singer|grid_ls:2.6;anchors:per_word;legato:all_notes;vibrato:halved_on_holds|approved engine treatment; compress never stretch|Greg v7
S002|2026-11-23|singer|rule:serve_original_melody|never author over the song|user via Greg v7
S003|2026-11-23|singer|order:pairs_chorus_verses;cadence:one_variable_per_take|ship in user's review order|Greg v7
S004|2026-11-23|piper|bug:phonemizer_mojibake;symbols: StressUP,U0254,U026A;fix:aligned_voice_MOJIBAKE_table|this PC phonemizer mangles 3 phonemes; dropped ids = wrong words + broken alignment|Greg v8
S005|2026-11-23|piper|bug:silent_fallback;check:nuclei_count==spans_count|empty phoneme_alignments routes every clip to abandoned runs-mapping (garbles); verify before trusting a take|Greg v8
S006|2026-11-23|voice|jeff:bryce;reason:only_bryce_sings_his_cleanly;rejected:amy,patrick,bobby,ryan_high|user ear A/B on D0|Greg v8
S007|2026-11-23|singer|bug:punch_pop;site:diphthong_glide(A0 gay);fix:flag_keep_last_pitch;v2:hold_ratio_through_unvoiced|v1 zeroed unvoiced source frames = vowel cut in/out; interp-hold fixed the pop (user: gone)|Greg v8
S008|2026-11-23|singer|fix:_declick;rule:3ms_fade_in_after_30ms_gap|warp leaves silent holes; voice pops in at full level|Greg v8
S009|2026-11-23|piper|limit:faster_whisper_unusable;fails_on:approved_takes|user ear is the only judge on this PC|Greg v8
S010|2026-11-23|song|lyrics:B3_B7_tag3=fuck_im_so_gay;C4=suck;C6=straight|user lyrics 2026-11-23|user
S011|2026-11-23|song|verse3:vD_after_chorus2;melody:vC_verbatim;lines:D0_D2_D4_D6|user lyrics; renders need re-approve|Greg v8
S012|2026-11-23|song|im_schwa:root_cause_phonics_sheet;am:say_im_too_broad;fix:am->æm in data_phonics;status:A0_take9_awaiting_ear|'I em Jeff' was the sheet's am->/ɪm/ entry (old I'm fix), not Piper|Greg v8
S013|2026-11-23|process|rule:document_on_the_spot;location:docs/FINDINGS.md|user rule|user
S014|2026-11-23|process|method:raw_speech_AB;separates:engine_vs_piper_artifact|clean raw + pop sung = engine pitch flattening|Greg v8
S015|2026-11-23|singer|flag:no_melisma;flag:rel(i)|optional per-line switches; rel = tail trim, no accent|Greg v8
S016|2026-11-23|tool|new_voicebank_location:tools/models/;needs:onnx+onnx_json_pair|added bobby+patrick 2026-11-23|Greg v8
S017|2026-11-23|process|pattern:symptom_cause_fix|records that store all three let the next session pattern-match instead of re-diagnose|Greg v8
S018|2026-11-23|process|rule:record_unverified_with_claim|every claim carries its verification status; untested = never trusted, never re-tested blindly|Greg v8
S019|2026-11-23|process|domain:open;use:pending_user_decisions|open-question records so a session resumes mid-thought|Greg v8
S020|2026-11-23|song|unverified:all_bryce_renders_by_ear;verified:mojibake_fix_nuclei7v7,declick_measurement|nothing sung today is user-approved except A0 take7 pending|Greg v8
S021|2026-11-23|song|approved_lines:A0,A2,A4(take4_patrick),A6;open:verse1_SECTION_approval;open:chorus1_section_review|rule:whole section approved together before moving on, separate from line approvals|user via Greg v8
S022|2026-11-23|singer|pattern:symptom_cause_fix;case:rushed_first_word(A4 Jake's);fix:keep_first_pitch,no_scoop|first-word rush = entrance scoop + flattened note fighting the voice's natural attack; mirror of keep_last_pitch|Greg v8
S023|2026-11-23|singer|pattern:symptom_cause_fix;case:schwa_reduction(A6 to_make->ta);fix:say_tou+glide[0,1]|'to,','too','two','toe','took' all failed; 'tou' keeps stressed u inside one sentence; comma splits chunks and kills melody|Greg v8
S024|2026-11-23|singer|rule:glide_cuts_word_i_end;place_breath_after_rushed_word_not_before|glide[0,1] trimmed Jake's tail and read as rushed; moved to [1,2]|Greg v8
S025|2026-11-23|process|rule:section_approval_separate_from_lines|user approves whole sections together before moving on|user
S026|2026-11-23|voice|verse_mix:bryce(A0,A2)+patrick(A4,A6);a4_bryce_was_approved_then_swapped|user ear picked patrick for A4/A6|userS027|2026-11-23|game|pattern:symptom_cause_fix;symptom:hands_detached,fingers_like_sticks_in_game;cause:code_neutral!=file_rest(joint_swings_by_(R-I)*t,t=code_joint_origin-file_bone_origin,up_to_32cm);fix:rigref_captures_file_A-pose_rest+data/character_offsets.json;check:tools/hero_rig/v8/tools_t.py=0.0cm;ruled_out:bone_roll(world_axes,wasted_hours);status:verified_body_joints_0.0cm,hands_on_wrists_hula+flex_renders|never rotate or re-roll bones before comparing code neutral to file rest|Wren v8
S028|2026-11-23|game|rule:face_joints_driven_every_frame_ignore_character_offsets.json;fix:set_consts(EYE_X=0.0481,EYE_Y=0.0165,EYE_Z=0.076,EYE_R=0.0305)+put_Blender_bones_on_same_points;catchlights:mesh+bone_at_code_neutral_taken_from_character_rig.json;status:verified_tools_t_0.0cm(white,lid,iris,pupil,shine)+5_expression_renders|eyes floated outside sockets because code constants described the old head sculpt|Wren v8
S029|2026-11-23|model|pattern:symptom_cause_fix;symptom:hollow_face,neck_tube_visible_through_face;cause:head_12_normals_inward(16329_of_16386);fix:bmesh_reverse_faces;check:count_normals_vs_part_centre_before_export;status:verified_render|game culls back faces; glTF is single sided|Wren v8
S030|2026-11-23|model|open:neck_1_reaches_z1.586_(eye_level)_inside_head;open:face_joints_1-5cm_off_(~90:mustache,lips,nose,cheeks);open:patchy_face_texture,hair_over_forehead,neck_colour;open:belt,buttons,collar_missing_on_new_torso;open:thigh_r_2_sliver_29mm;open:eyes_30pct_bigger_than_shipped;status:unverified_on_phone|next: align face joints (mustache first) to tools_t 0.0cm|Wren v8
S031|2026-11-23|tool|pipeline:blend_to_glb->godot_--import->rigref->tools_t->smoke->xvfb_renders;godot:4.6.3_headless;files:tools/hero_rig/v8/(README);branch:wren-hero-wip@42d9c73(non-building)|rerun rigref+tools_t after EVERY glb export|Wren v8
S032|2026-11-23|process|rule:sliders_sheet_shared_both_agents;url:claude.ai/artifact/DCtcGk9epuFbcysKLewoAX;edit:own_tabs_only;show_in_chat_when_PERSONALITIES_written|user: "this is for both you guys to edit. not just you"|user via Wren v8
S033|2026-11-23|process|rename:Process_overhead->Rule_enforcement(Wren_set,50);reason:user_wrote_the_rules_so_low_never_meant_resent;voice_rule:<50_minimal_process_talk,>=50_full_visibility|slider labels must describe the user's behaviour, not my lapses|Wren v8
S034|2026-11-23|process|open:user_asked_where_old_Findings_memory_bank_was;found:docs/FINDINGS.md_pushed_by_Greg_mid_session(e22805b);lesson:git_fetch_origin/godot_before_saying_a_file_does_not_exist|I told the user it did not exist from a stale worktree|Wren v8
