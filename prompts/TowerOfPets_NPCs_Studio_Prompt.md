I imported 12 NPC models into Roblox Studio from FBX with the 3D Importer. Each one is a Model named after its file: "Shop_NPC", "Egg_NPC", "Trading_NPC", "Upgrades_NPC", "Pets_NPC", "Leaderboards_NPC", "Tower_Guide_NPC", "Tower_Entrance_NPC", "Codes_NPC", "Daily_Rewards_NPC", "Index_NPC", "Settings_NPC". Each Model is made of MeshParts.

Write me ONE Studio command-bar script that sets up all 12 NPCs. Wrap everything in ChangeHistoryService so I can undo it. Find each Model anywhere in Workspace by name (ignore case), and skip any NPC that isn't there with a warning.

STEP 1 - COLOURS
- Colour every MeshPart by its exact Name (ignore case). Do NOT match by prefix: "Head" and "Head_Hair" are different parts.
- For every listed part, set Color = Color3.fromRGB(r, g, b), set TextureID = "" and remove any SurfaceAppearance child.
- Material is SmoothPlastic, except parts marked NEON, which get Enum.Material.Neon.
- The same part name means different colours in different NPCs, so use each NPC's own list below.

STEP 2 - ASSEMBLE EACH NPC SO IT MOVES AS ONE
- Body parts use Roblox R15 names: Head, UpperTorso, LowerTorso, LeftUpperArm, LeftLowerArm, LeftHand, RightUpperArm, RightLowerArm, RightHand, LeftUpperLeg, LeftLowerLeg, LeftFoot, RightUpperLeg, RightLowerLeg, RightFoot.
- Every other part is named <BodyPart>_<Item> (for example "LeftHand_PropStaff" or "Head_HatBrim"). The text before the first "_" is the body part it belongs to.
- Weld each item to its body part with a WeldConstraint, and weld every body part to LowerTorso.
- Set the Model's PrimaryPart to LowerTorso. Anchor only LowerTorso.
- Set CanCollide = false and CanTouch = false on every part except UpperTorso and LowerTorso. Set CastShadow = false on NEON parts.
- If a Model's height (from GetExtentsSize) is not between 5 and 7.5 studs, the import scale was wrong. Scale it with Model:ScaleTo so the body is 5.3 studs tall without the hat. The Blender model is 1.49 m to the top of the head, at 1 stud = 0.28 m.
- Don't create a Humanoid or move the NPCs. Keep them exactly where they are.

STEP 3 - REPORT
Print, per NPC, how many parts were coloured, how many were welded, and any MeshPart whose name wasn't in that NPC's list.

PART COLOURS (r, g, b):

01 SHOP - Model "Shop_NPC"
- (232, 178, 62) Gold: Head_HatBand, Head_HatFlower, Head_HatRim, LeftLowerArm_GloveTrim, LowerTorso_Buckle, LowerTorso_CoatTailEdgeTrim, LowerTorso_CoatTailHem, LowerTorso_PouchClaspLeft, LowerTorso_PouchClaspRight, RightLowerArm_GloveTrim, UpperTorso_CapeletEdgeTrim, UpperTorso_CapeletHem, UpperTorso_FrontTrim, UpperTorso_Lacing1, UpperTorso_Lacing2, UpperTorso_Lacing3, UpperTorso_Lacing4, UpperTorso_Lacing5, UpperTorso_Lacing6
- (206, 38, 36) Red: Head_HatBrim, Head_HatCrown, LeftLowerArm, LeftUpperArm, LeftUpperArm_Sleeve, LowerTorso_CoatTail, RightLowerArm, RightUpperArm, RightUpperArm_Sleeve, UpperTorso_Capelet, UpperTorso_Coat
- (40, 33, 35) Black: Head_HatBrimUnder, LeftLowerLeg, LeftUpperLeg, LowerTorso, RightLowerLeg, RightUpperLeg, UpperTorso, UpperTorso_Collar, UpperTorso_Vest
- (36, 33, 38) Glove Black: LeftFoot, LeftHand, LeftLowerArm_Glove, RightFoot, RightHand, RightLowerArm_Glove
- (28, 24, 28) Face Black: Head_Eye_Left, Head_Eye_Right, Head_Smile
- (104, 64, 38) Leather Brown: LowerTorso_Belt, LowerTorso_PouchLeft, LowerTorso_PouchRight
- (255, 206, 72) FeatherYellow: Head_HatFeather_2, Head_HatFeather_3
- (30, 28, 34) Hair: Head_Hair, Head_HairBase
- (246, 204, 166) Skin: Head
- (242, 240, 234) White: UpperTorso_ShirtCollar
- (250, 150, 44) FeatherOrange: Head_HatFeather_1

02 EGG - Model "Egg_NPC"
- (236, 140, 255) NEON EggGlow: RightHand_PropEgg
- (130, 58, 192) Purple: LeftLowerArm, LeftLowerArm_SleeveWide, LeftUpperArm, LeftUpperArm_Sleeve, LowerTorso_Robe, RightLowerArm, RightLowerArm_SleeveWide, RightUpperArm, RightUpperArm_Sleeve, UpperTorso_Cloak, UpperTorso_Mantle, UpperTorso_Robe
- (232, 178, 62) Gold: LeftLowerArm_Cuff, LowerTorso_Buckle, LowerTorso_RobeEdgeTrim, LowerTorso_RobeHem, RightLowerArm_Cuff, UpperTorso_CloakEdgeTrim, UpperTorso_CloakHem, UpperTorso_Emblem, UpperTorso_FrontTrim, UpperTorso_MantleEdgeTrim, UpperTorso_MantleHem
- (36, 33, 38) Glove Black: LeftFoot, LeftHand, LeftLowerLeg, LeftUpperLeg, LowerTorso_UnderskirtStripe, RightFoot, RightHand, RightLowerLeg, RightUpperLeg
- (62, 30, 102) PurpleDark: LowerTorso, LowerTorso_Belt, UpperTorso, UpperTorso_Collar, UpperTorso_RobeFront
- (28, 24, 28) Face Black: Head_Eye_Left, Head_Eye_Right, Head_Smile
- (242, 240, 234) White: LowerTorso_Underskirt, UpperTorso_EmblemGem
- (214, 190, 238) Hair: Head_Hair, Head_HairBase
- (246, 204, 166) Skin: Head
- (176, 86, 236) Gem: LowerTorso_BeltGem

03 TRADING - Model "Trading_NPC"
- (232, 178, 62) Gold: LeftLowerArm_CuffTrim, LowerTorso_Buckle, LowerTorso_CoatTailEdgeTrim, LowerTorso_CoatTailHem, LowerTorso_SatchelClasp, RightLowerArm_CuffTrim, UpperTorso_ButtonLeft1, UpperTorso_ButtonLeft2, UpperTorso_ButtonLeft3, UpperTorso_ButtonRight1, UpperTorso_ButtonRight2, UpperTorso_ButtonRight3, UpperTorso_CapeletEdgeTrim, UpperTorso_CapeletHem, UpperTorso_FrontTrim, UpperTorso_Medal, UpperTorso_ShoulderButton
- (242, 240, 234) White: LeftLowerArm, LeftUpperArm, LowerTorso_ShirtTail, RightLowerArm, RightUpperArm, UpperTorso, UpperTorso_Collar, UpperTorso_Shirt
- (78, 50, 32) Brown: LeftLowerLeg, LeftUpperLeg, LowerTorso, LowerTorso_CoatTail, RightLowerLeg, RightUpperLeg, UpperTorso_Coat
- (36, 33, 38) Glove Black: LeftFoot, LeftHand, LeftLowerArm_Glove, RightFoot, RightHand, RightLowerArm_Glove
- (104, 64, 38) Leather Brown: Head_HatBand, LowerTorso_Belt, LowerTorso_SatchelFlap, UpperTorso_SatchelStrap
- (28, 24, 28) Face Black: Head_Eye_Left, Head_Eye_Right, Head_Smile
- (142, 90, 48) BrownLight: LowerTorso_Satchel, UpperTorso_VestLeft, UpperTorso_VestRight
- (214, 164, 72) Brass: Head_GoggleBridge, Head_GoggleLeft, Head_GoggleRight
- (34, 30, 30) HatBlack: Head_HatBrim, Head_HatCrown
- (255, 214, 140) Lens: Head_GoggleLensLeft, Head_GoggleLensRight
- (130, 76, 40) Hair: Head_Hair, Head_HairBase
- (246, 204, 166) Skin: Head
- (168, 92, 40) Rust: UpperTorso_Capelet

04 UPGRADES - Model "Upgrades_NPC"
- (70, 170, 255) NEON CrystalGlow: LeftHand_PropCrystal
- (242, 240, 234) White: LeftLowerArm, LeftLowerArm_SleeveWide, LeftUpperArm, LeftUpperArm_Sleeve, LowerTorso_Underskirt, RightLowerArm, RightLowerArm_SleeveWide, RightUpperArm, RightUpperArm_Sleeve, UpperTorso, UpperTorso_Cloak, UpperTorso_Shirt
- (36, 80, 198) Blue: Head_HatBrim, Head_HatCone, LeftLowerArm_Cuff, LeftLowerLeg, LeftUpperLeg, LowerTorso, LowerTorso_Robe, RightLowerArm_Cuff, RightLowerLeg, RightUpperLeg, UpperTorso_Robe
- (232, 178, 62) Gold: LeftLowerArm_CuffTrim, LowerTorso_Buckle, LowerTorso_RobeEdgeTrim, LowerTorso_RobeHem, RightLowerArm_CuffTrim, RightUpperArm_Pauldron, RightUpperArm_PauldronRidge, UpperTorso_Brooch, UpperTorso_CloakEdgeTrim, UpperTorso_CloakHem, UpperTorso_FrontTrim
- (246, 204, 166) Skin: Head, LeftHand, RightHand
- (22, 44, 118) BlueDark: LeftFoot, LowerTorso_Belt, RightFoot
- (28, 24, 28) Face Black: Head_Eye_Left, Head_Eye_Right, Head_Smile
- (70, 150, 255) Gem: LowerTorso_BeltGem, UpperTorso_BroochGem
- (228, 232, 248) Hair: Head_Hair, Head_HairBase
- (66, 44, 34) Wood Dark: LeftHand_PropStaff, LeftHand_PropStaffClaws
- (248, 202, 82) Bow: Head_HatBow

05 PETS - Model "Pets_NPC"
- (60, 230, 110) NEON LeafGlow: RightHand_PropLeafCrystal
- (232, 178, 62) Gold: Head_Antlers, LeftLowerArm_Bracer, LowerTorso_Buckle, LowerTorso_DressEdgeTrim, LowerTorso_DressHem, RightLowerArm_Bracer, UpperTorso_CapeletEdgeTrim, UpperTorso_CapeletHem, UpperTorso_LeafBrooch, UpperTorso_VTrim
- (24, 92, 44) GreenDark: LeftFoot, LeftHand, LeftLowerLeg, LeftUpperLeg, RightFoot, RightHand, RightLowerLeg, RightUpperLeg
- (246, 204, 166) Skin: Head, LeftLowerArm, LeftUpperArm, RightLowerArm, RightUpperArm
- (40, 142, 64) Green: LowerTorso, LowerTorso_Dress, UpperTorso, UpperTorso_Capelet, UpperTorso_Dress
- (28, 24, 28) Face Black: Head_Eye_Left, Head_Eye_Right, Head_Smile
- (98, 186, 64) Leaf: Head_LeafCrown, LeftHand_PropBranchLeaves, RightHand_PropStaffLeaves
- (242, 232, 205) Cream: LowerTorso_Underskirt, UpperTorso_Shirt
- (60, 210, 110) Gem: LowerTorso_BeltGem, UpperTorso_LeafBroochGem
- (36, 112, 50) Hair: Head_Hair, Head_HairBase
- (66, 44, 34) Wood Dark: LeftHand_PropBranch, RightHand_PropStaff
- (104, 64, 38) Leather Brown: LowerTorso_Belt

06 LEADERBOARDS - Model "Leaderboards_NPC"
- (232, 178, 62) Gold: Head_CrownOrbs, Head_CrownRimLower, Head_CrownRimUpper, Head_CrownSpikes, LowerTorso_Belt, LowerTorso_Buckle, LowerTorso_SkirtHem, LowerTorso_SkirtStripe1, LowerTorso_SkirtStripe2, LowerTorso_SkirtStripe3, LowerTorso_SkirtStripe4, UpperTorso_CapeEdgeTrim, UpperTorso_CapeHem, UpperTorso_Emblem, UpperTorso_EmblemWingLeft, UpperTorso_EmblemWingRight, UpperTorso_FrontTrim, UpperTorso_FurMantleEdgeTrim, UpperTorso_FurMantleHem
- (32, 66, 182) Blue: Head_CrownBand, LeftLowerArm_CuffBand, LeftLowerArm_SleeveBand, LeftLowerLeg, LeftUpperLeg, LowerTorso, LowerTorso_Skirt, RightLowerArm_CuffBand, RightLowerArm_SleeveBand, RightLowerLeg, RightUpperLeg, UpperTorso, UpperTorso_CapeStripe, UpperTorso_Collar, UpperTorso_Tunic, UpperTorso_TunicFront
- (242, 240, 234) White: LeftLowerArm, LeftLowerArm_SleeveWide, LeftUpperArm, LeftUpperArm_Sleeve, RightLowerArm, RightLowerArm_SleeveWide, RightUpperArm, RightUpperArm_Sleeve, UpperTorso_Cape, UpperTorso_FurMantle
- (246, 204, 166) Skin: Head, LeftHand, RightHand
- (28, 24, 28) Face Black: Head_Eye_Left, Head_Eye_Right, Head_Smile
- (90, 170, 255) Gem: Head_CrownGems, LowerTorso_BeltGem, UpperTorso_EmblemGem
- (22, 40, 120) BlueDark: LeftFoot, RightFoot
- (230, 196, 140) Hair: Head_Hair, Head_HairBase

07 TOWER GUIDE - Model "Tower_Guide_NPC"
- (70, 180, 255) NEON PawGlow: LeftHand_PropPawGlow
- (242, 240, 234) White: Head_HatBand, LeftLowerArm, LeftLowerLeg_PantsCuff, LeftUpperArm_SleeveCuff, LowerTorso_CoatTailEdgeTrim, LowerTorso_CoatTailHem, RightLowerArm, RightLowerLeg_PantsCuff, RightUpperArm_SleeveCuff, UpperTorso, UpperTorso_Cape, UpperTorso_FrontTrim, UpperTorso_Shirt
- (40, 94, 208) Blue: Head_HatBrim, Head_HatCone, LeftLowerLeg, LeftUpperArm, LeftUpperLeg, LowerTorso, LowerTorso_CoatTail, RightLowerLeg, RightUpperArm, RightUpperLeg, UpperTorso_CapeEdgeTrim, UpperTorso_CapeHem, UpperTorso_Coat
- (246, 204, 166) Skin: Head, LeftHand, RightHand
- (28, 24, 28) Face Black: Head_Eye_Left, Head_Eye_Right, Head_Smile
- (26, 56, 140) BlueDark: LeftFoot, RightFoot
- (232, 178, 62) Gold: LowerTorso_Buckle, RightHand_PropBookTrim
- (238, 238, 244) Hair: Head_Hair, Head_HairBase
- (104, 64, 38) Leather Brown: LowerTorso_Belt
- (112, 66, 36) Book: RightHand_PropBook
- (246, 236, 212) Pages: RightHand_PropBookPages

08 TOWER ENTRANCE - Model "Tower_Entrance_NPC"
- (110, 200, 255) NEON EyeGlow: Head_EyeGlow_Left, Head_EyeGlow_Right
- (80, 180, 255) NEON PawGlow: UpperTorso_PawEmblem, UpperTorso_RuneLines
- (28, 30, 50) Coat: LeftLowerArm, LeftLowerArm_SleeveFlare, LeftLowerLeg, LeftUpperArm, LeftUpperArm_Sleeve, LeftUpperLeg, LowerTorso, LowerTorso_LongCoat, RightLowerArm, RightLowerArm_SleeveFlare, RightLowerLeg, RightUpperArm, RightUpperArm_Sleeve, RightUpperLeg, UpperTorso_Coat
- (222, 144, 64) Trim: Head_HoodTrim, LeftLowerArm_CuffTrim, LowerTorso_LongCoatEdgeTrim, LowerTorso_LongCoatHem, RightLowerArm_CuffTrim, UpperTorso_FrontTrim, UpperTorso_HoodMantleEdgeTrim, UpperTorso_HoodMantleHem
- (36, 33, 38) Glove Black: LeftFoot, LeftHand, RightFoot, RightHand
- (34, 60, 150) Inner: LowerTorso_InnerRobe, UpperTorso, UpperTorso_Shirt
- (42, 72, 176) Hood: Head_Hood, UpperTorso_HoodMantle
- (6, 6, 14) FaceVoid: Head

09 CODES - Model "Codes_NPC"
- (170, 80, 250) NEON GiftGlow: LeftHand_PropGift, LeftHand_PropSparkles
- (255, 240, 255) NEON Ribbon: LeftHand_PropGiftRibbon
- (34, 28, 40) Black: LeftFoot, LeftHand, LeftLowerArm, LeftLowerLeg, LeftUpperLeg, LowerTorso, LowerTorso_Belt, RightFoot, RightHand, RightLowerArm, RightLowerLeg, RightUpperLeg, UpperTorso, UpperTorso_Shirt
- (206, 158, 238) Lavender: LeftUpperArm, LeftUpperArm_PuffSleeve, LowerTorso_JacketHem, RightUpperArm, RightUpperArm_PuffSleeve, UpperTorso_Jacket
- (232, 178, 62) Gold: Head_HairBow, LeftUpperArm_SleeveTrim, LowerTorso_Buckle, LowerTorso_JacketHemEdgeTrim, LowerTorso_JacketHemHem, RightUpperArm_SleeveTrim
- (28, 24, 28) Face Black: Head_Eye_Left, Head_Eye_Right, Head_Smile
- (244, 178, 226) Pink: UpperTorso_Collar, UpperTorso_FrontTrim
- (94, 42, 158) Hair: Head_Hair, Head_HairBase
- (246, 204, 166) Skin: Head

10 DAILY REWARDS - Model "Daily_Rewards_NPC"
- (255, 236, 180) NEON CalendarGrid: LeftHand_PropCalendarGrid, LeftHand_PropCalendarRings
- (255, 150, 40) NEON CalendarGlow: LeftHand_PropCalendar
- (32, 28, 32) Black: LeftHand, LeftLowerArm, LeftLowerLeg, LeftUpperArm, LeftUpperLeg, LowerTorso, LowerTorso_CoatTail, RightHand, RightLowerArm, RightLowerLeg, RightUpperArm, RightUpperLeg, UpperTorso, UpperTorso_Jacket
- (234, 124, 34) Orange: LowerTorso_CoatTailEdgeTrim, LowerTorso_CoatTailHem, LowerTorso_OrangeFlapLeft, LowerTorso_OrangeFlapRight, UpperTorso_Capelet, UpperTorso_Scarf, UpperTorso_ScarfTail, UpperTorso_Vest
- (232, 178, 62) Gold: UpperTorso_CapeletEdgeTrim, UpperTorso_CapeletHem, UpperTorso_Embroidery1, UpperTorso_Embroidery2, UpperTorso_Embroidery3, UpperTorso_FrontTrim
- (28, 24, 28) Face Black: Head_Eye_Left, Head_Eye_Right, Head_Smile
- (104, 64, 38) Leather Brown: LeftFoot, RightFoot
- (242, 226, 200) Cream: LeftLowerArm_CreamBand, RightLowerArm_CreamBand
- (216, 104, 40) Hair: Head_Hair, Head_HairBase
- (246, 204, 166) Skin: Head

11 INDEX - Model "Index_NPC"
- (70, 175, 255) NEON Glow: LeftHand_PropTabletPaw, LowerTorso_BackBow, LowerTorso_CoatTailEdgeTrim, LowerTorso_CoatTailHem, UpperTorso_FrontTrim, UpperTorso_PawEmblem
- (34, 84, 214) NEON TabletScreen: LeftHand_PropTabletScreen
- (24, 24, 30) Black: LeftFoot, LeftHand, LeftLowerLeg, LeftUpperLeg, RightFoot, RightHand, RightLowerLeg, RightUpperLeg
- (28, 34, 66) Navy: LeftLowerArm, LeftUpperArm, LowerTorso, LowerTorso_CoatTail, RightLowerArm, RightUpperArm, UpperTorso_Coat
- (242, 240, 234) White: LeftLowerArm_WhiteBand, LeftLowerLeg_WhiteBand, RightLowerArm_WhiteBand, RightLowerLeg_WhiteBand, UpperTorso, UpperTorso_Shirt
- (28, 24, 28) Face Black: Head_Eye_Left, Head_Eye_Right, Head_Glasses, Head_Smile
- (24, 24, 34) Hair: Head_Hair, Head_HairBase
- (246, 204, 166) Skin: Head
- (104, 64, 38) Leather Brown: LowerTorso_Belt
- (232, 178, 62) Gold: LowerTorso_Buckle
- (40, 52, 112) TabletFrame: LeftHand_PropTablet

12 SETTINGS - Model "Settings_NPC"
- (22, 64, 150) NEON HoloPanel: LeftHand_PropHoloPanel_1, LeftHand_PropHoloPanel_2
- (70, 175, 255) NEON HoloGlow: LeftHand_PropHoloIcons_1, LeftHand_PropHoloIcons_2
- (30, 30, 36) Black: LeftFoot, LeftHand, LeftLowerArm, LeftLowerLeg, LeftUpperArm, LeftUpperLeg, LowerTorso, LowerTorso_Belt, LowerTorso_CoatTail, RightFoot, RightHand, RightLowerArm, RightLowerLeg, RightUpperArm, RightUpperLeg, UpperTorso_Coat
- (238, 238, 242) White: LeftLowerArm_WhiteBand, LeftUpperArm_UpperBand, LowerTorso_CoatTailEdgeTrim, LowerTorso_CoatTailHem, RightLowerArm_WhiteBand, RightUpperArm_ShoulderPad, UpperTorso, UpperTorso_Shirt, UpperTorso_WhitePanelLeft, UpperTorso_WhitePanelRight
- (28, 24, 28) Face Black: Head_Eye_Left, Head_Eye_Right, Head_Smile
- (30, 36, 62) Strap: Head_GoggleFrameLeft, Head_GoggleFrameRight, Head_GoggleStrap
- (152, 154, 164) Grey: RightUpperArm_PadStripe, UpperTorso_FrontTrim
- (60, 122, 212) GoggleLens: Head_GoggleLensLeft, Head_GoggleLensRight
- (236, 236, 244) Hair: Head_Hair, Head_HairBase
- (246, 204, 166) Skin: Head
- (232, 178, 62) Gold: LowerTorso_Buckle
