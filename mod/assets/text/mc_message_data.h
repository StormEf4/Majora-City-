/**
 * Majora City text bank. Included from assets/text/message_data.h (see patches/).
 *
 * IDs 0x4D00-0x4DFF are reserved for Majora City. tools/check.sh verifies they don't collide with the vanilla
 * messages once the ROM's text has been extracted. Matching #defines live in mod/include/mc/mc.h.
 *
 * Header: HEADER(textBoxProperties, itemId, nextTextId, firstChoicePrice, secondChoicePrice, unk)
 *   textBoxProperties: 0x0C00 = scene title card, 0x0500 = clear box (no background), 0x0000 = black box
 */

// MC_TEXT_TITLE_MAJORA_CITY: shown with Message_DisplaySceneTitleCard over the skyline
DEFINE_MESSAGE(0x4D00, 0x00, 0x00,
MSG(
HEADER(0x0C00, 0xFE, 0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF)
"Majora City"
)
)

// MC_TEXT_INTRO_NARRATION_1
DEFINE_MESSAGE(0x4D01, 0x00, 0x00,
MSG(
HEADER(0x0500, 0xFE, 0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF)
"Three days' ride from Hyrule," NEWLINE
"the old trade road to Termina" NEWLINE
"turned to stone..." FADE(40)
)
)

// MC_TEXT_INTRO_NARRATION_2
DEFINE_MESSAGE(0x4D02, 0x00, 0x00,
MSG(
HEADER(0x0500, 0xFE, 0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF)
"...then to steel." FADE(50)
)
)
