# FINDINGS BANK v2
# Greg's bank, PRIVATE to Greg (user rule 2026-11-23: agents do not share memories or read each other's). Write on the spot
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
S021|2026-11-23|song|approved_sections:verse1(A0,A2,A4,A6);open:chorus1_section_review;open:C_D_tag_F_sections|verse1 pushed to phone via CI smoke gate; line approvals carried over|user via Greg v8
S022|2026-11-23|singer|pattern:symptom_cause_fix;case:rushed_first_word(A4 Jake's);fix:keep_first_pitch,no_scoop|first-word rush = entrance scoop + flattened note fighting the voice's natural attack; mirror of keep_last_pitch|Greg v8
S023|2026-11-23|singer|pattern:symptom_cause_fix;case:schwa_reduction(A6 to_make->ta);fix:say_tou+glide[0,1]|'to,','too','two','toe','took' all failed; 'tou' keeps stressed u inside one sentence; comma splits chunks and kills melody|Greg v8
S024|2026-11-23|singer|rule:glide_cuts_word_i_end;place_breath_after_rushed_word_not_before|glide[0,1] trimmed Jake's tail and read as rushed; moved to [1,2]|Greg v8
S025|2026-11-23|process|rule:section_approval_separate_from_lines|user approves whole sections together before moving on|user
S026|2026-11-23|voice|verse_mix:bryce(A0,A2)+patrick(A4,A6);a4_bryce_was_approved_then_swapped|user ear picked patrick for A4/A6|user
S027|2026-11-24|process|rule:checklist_step6_posts_sliders_in_chat_not_only_in_file;v2:POST_the_spreadsheet_file;v3:categories_match_across_agents;v4:FORMAT=Wren's_screenshot;v5:header_neutral_grey_no_green_bar|attach the actual file, styled: neutral grey header (solid green header too loud, pale green blends - both rejected), mint param column, Now cells green_up/red_down/white_zero, purple Why, blue hl row; Parameter|Before|Now|Change(+/-)|Why; dots kept; reference greg_v8_sliders.html|user
S028|2026-11-24|game|removed:embedded_piper;files:android/piper,piper.gd,piper-apk.yml,AndroidPiper_preset;reason:no_consumer_after_editor_removal;apk_slim:~77MB|user decision; edited words now play diphone bank or shipped clip; PIPER_ANDROID.md kept as record|Greg v8
S029|2026-11-24|piper|status:removed_from_apk;survives:tools/piper_sing.py_pc_only,docs/PIPER_ANDROID.md,git_history|desktop re-sing unaffected (python piper, never used the APK)|Greg v8
S030|2026-11-24|model|gotcha:shape_key_basis_overrides_base_mesh;mesh:head_12;fix:write_Basis.data_after_v_co_edit;cost:6_render_passes|evaluated render uses the Basis key copy, not edited v.co; measured EVAL zmax 1.738 vs base 1.730|Greg v9
S031|2026-11-24|model|fail:procedural_hair_x8;cards=wires_or_gaps;shell=hood;locks=tentacles;hair_lives_in:hero3d.gd__hair_cap+locks|8 parameter passes on blend hair all failed; the game builds its own hair in code, so fix the consumer or hand-sculpt|Greg v9
S032|2026-11-24|model|method:least_squares_face_fit;case:nose_shell_roots;fail:pointwise_min_lookup=stepped_seams;fix:quadratic_y(x,z)_fit+lift_1.5mm_proportional|bolted-on shells must root on a smooth fitted surface; raw vertex lookups z-fight|Greg v9
S033|2026-11-24|model|v68_numbers:head_wid_eye_217mm->192mm;hat_*_removed:5912_faces;total_100314->~82800;new:ear_l/r_0+nose_geo_rigged_to_head|human-proportion pass approved by user eye; profile refs converged it in one round|Greg v9
S034|2026-11-24|singer|fact:vox_head_drift=0.03..0.54s;engine_lead=0.15s;error=up_to_+390ms(D4);fix=align_head_to_0.15s+per_clip_lead|engine starts a clip 0.15 s before the bar and assumes the sound is there|Greg v11
S035|2026-11-24|piper|fact:bryce_id_map_lacks_U028C;mojibake=cp1252(U+0152);latin1_repair_fails;fix=cp1252_decode+fallback_ʌ->ɐ+guard_raises_on_unknown|'fuck' sang as fk and nothing reported it|Greg v11
S036|2026-11-24|song|fact:JSON_string_bar_fails_typed_int;effect=no_vox_key_silent;fact:chorus=v-B_bars0-7_E0-E3;B0-B3+B4/B5/B7_unused;fact:capture_dropout_once_rms_-12dB|check onset positions after every mix render|Greg v11
S037|2026-11-24|singer|fact:stretched_source_contour_over_hold=slow_seesaw('neigh');fix=steady_hold_note+vibrato<=14c_late|the old keep_last_pitch stretched a 0.35 s gay over 3.19 s|Greg v11
