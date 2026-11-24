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
S027|2026-11-24|process|rule:checklist_step6_posts_sliders_in_chat_not_only_in_file|file = record, chat = deliverable; both, every session end (user caught the miss)|user
S026|2026-11-23|voice|verse_mix:bryce(A0,A2)+patrick(A4,A6);a4_bryce_was_approved_then_swapped|user ear picked patrick for A4/A6|user
