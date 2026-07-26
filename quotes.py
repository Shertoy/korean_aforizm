# -*- coding: utf-8 -*-
"""
Tasdiqlangan koreys maqollari bazasi.
Har bir yozuv haqiqiy, keng tarqalgan koreys maqoli/idiomasidir — soxta yoki
noaniq muallif iqtiboslari emas. Yangi maqol qo'shishda ham xuddi shu
tamoyilga amal qilinsin: faqat tasdiqlangan, umumiy koreys xalq maqollari
yoki 한자성어 (xitoycha-koreyscha idiomalar) ishlatiladi.

Har bir maqolda:
- korean: asl koreyscha matn
- breakdown: [(koreyscha bo'lak, o'zbekcha ma'no), ...]  -- so'zma-so'z tarjima uchun
- grammar_note: grammatik izoh (o'zbek tilida)
- translation: to'liq o'zbekcha tarjima
- slot: "ertalab" yoki "kechqurun"
- reflection: faqat kechqurun uchun -- rasmga chiqadigan mulohaza savoli
- mood: rasm foni uchun uslub/kayfiyat tavsifi (inglizcha, rasm promptida ishlatiladi)
- hashtags: mavzuga mos hashtaglar ro'yxati
"""

QUOTES = [
    {
        "korean": "천 리 길도 한 걸음부터",
        "breakdown": [
            ("천 (cheon)", "ming"),
            ("리 (ri)", "\"li\" — qadimiy masofa o'lchovi (~0,4 km)"),
            ("길 (gil)", "yo'l"),
            ("도 (do)", "\"ham\" qo'shimchasi, urg'u beradi"),
            ("한 (han)", "bir"),
            ("걸음 (georeum)", "qadam"),
            ("부터 (buteo)", "\"-dan boshlab\" kelishik qo'shimchasi"),
        ],
        "grammar_note": (
            "도 qo'shimchasi \"hatto ... ham\" ma'nosini beradi — eng uzun yo'l "
            "ham istisno emasligini ta'kidlaydi. 부터 boshlanish nuqtasini "
            "bildiradi, o'zbekchadagi \"-dan\" kelishigiga mos keladi."
        ),
        "translation": "Ming li yo'l ham bir qadamdan boshlanadi.",
        "slot": "ertalab",
        "reflection": None,
        "mood": "sunrise mountain trail, first footprint in morning light, hopeful beginning",
        "hashtags": ["#harakat", "#maqsad", "#birinchiqadam"],
    },
    {
        "korean": "시작이 반이다",
        "breakdown": [
            ("시작 (sijak)", "boshlanish"),
            ("이 (i)", "ega qo'shimchasi"),
            ("반 (ban)", "yarim"),
            ("이다 (ida)", "\"-dir\" bog'lovchi fe'l"),
        ],
        "grammar_note": (
            "이다 — otni kesimga aylantiruvchi bog'lovchi fe'l, o'zbekchadagi "
            "\"-dir\" yuklamasiga teng. 이 esa ega qo'shimchasi bo'lib, gapning "
            "bosh bo'lagini ko'rsatadi."
        ),
        "translation": "Boshlash — ishning yarmi.",
        "slot": "ertalab",
        "reflection": None,
        "mood": "open door at dawn, warm light spilling onto a path, sense of starting fresh",
        "hashtags": ["#boshlanish", "#harakat", "#erinmaslik"],
    },
    {
        "korean": "구르는 돌에는 이끼가 끼지 않는다",
        "breakdown": [
            ("구르는 (gureuneun)", "aylanayotgan (fe'l sifatdoshi)"),
            ("돌 (dol)", "tosh"),
            ("에는 (eneun)", "\"-da/-ga\" o'rin qo'shimchasi + urg'u"),
            ("이끼 (ikki)", "moxlar"),
            ("가 (ga)", "ega qo'shimchasi"),
            ("끼지 않는다 (kkiji anneunda)", "bosib olmaydi (bo'lishsiz shakl)"),
        ],
        "grammar_note": (
            "않는다 — fe'lni inkor qiladigan qolip (\"안\" + fe'l yoki fe'l tagida "
            "\"-지 않다\"). Bu yerda \"끼지 않는다\" = \"bosib olmaydi\"."
        ),
        "translation": "Doim harakatdagi toshni mox bosmaydi.",
        "slot": "ertalab",
        "reflection": None,
        "mood": "smooth river stone in flowing water, motion and clarity, early daylight",
        "hashtags": ["#harakat", "#rivojlanish", "#toxtamaslik"],
    },
    {
        "korean": "세월이 유수와 같다",
        "breakdown": [
            ("세월 (sewol)", "vaqt, umr o'tishi"),
            ("이 (i)", "ega qo'shimchasi"),
            ("유수 (yusu)", "oqar suv (한자어, 流水)"),
            ("와 (wa)", "\"kabi/bilan\" solishtirish qo'shimchasi"),
            ("같다 (gatda)", "o'xshaydi, kabidir"),
        ],
        "grammar_note": (
            "와 qo'shimchasi ikki narsani solishtirishda ishlatiladi — "
            "\"X Y ga o'xshaydi\" qolipi. 같다 fe'li shu solishtirishni yakunlaydi."
        ),
        "translation": "Vaqt oqar suvga o'xshaydi.",
        "slot": "kechqurun",
        "reflection": "Siz bu oqimni nima bilan to'ldiryapsiz?",
        "reflection_ko": "지금 이 흐름을 무엇으로 채우고 계신가요?",
        "mood": "calm river at dusk, fading sunlight on water, quiet reflective atmosphere",
        "hashtags": ["#vaqt", "#hayot", "#mulohaza"],
    },
    {
        "korean": "빈손으로 왔다가 빈손으로 간다",
        "breakdown": [
            ("빈손 (binson)", "bo'sh qo'l"),
            ("으로 (euro)", "vosita/holat qo'shimchasi, \"bilan/holida\""),
            ("왔다가 (watdaga)", "kelib (o'tgan zamon + bog'lovchi)"),
            ("빈손으로 (binsoneuro)", "bo'sh qo'l bilan (takror)"),
            ("간다 (ganda)", "ketadi (hozirgi-kelasi zamon)"),
        ],
        "grammar_note": (
            "-다가 qo'shimchasi bir harakatdan ikkinchisiga o'tishni bildiradi. "
            "으로 esa \"qanday holatda\" ekanini ko'rsatuvchi vosita kelishigi."
        ),
        "translation": "Bo'sh qo'l bilan kelib, bo'sh qo'l bilan ketadi.",
        "slot": "kechqurun",
        "reflection": "Unda nimani ortda qoldirmoqchisiz?",
        "reflection_ko": "그렇다면 당신은 무엇을 남기고 싶으신가요?",
        "mood": "empty path leading toward a distant horizon at twilight, minimal and contemplative",
        "hashtags": ["#hayot", "#mulohaza", "#omonat"],
    },
    {
        "korean": "화무십일홍",
        "breakdown": [
            ("화 (hwa)", "gul (한자, 花)"),
            ("무 (mu)", "yo'q, -mas (한자, 無)"),
            ("십일 (sibil)", "o'n kun (十日)"),
            ("홍 (hong)", "qizillik, gullash (紅)"),
        ],
        "grammar_note": (
            "Bu 한자성어 (xitoycha-koreyscha to'rt bo'g'inli idioma) — har bir "
            "bo'g'in alohida ma'noli xitoycha belgiga asoslangan, alohida "
            "grammatik qo'shimcha yo'q, butun ibora bitta tayyor birlik sifatida "
            "ishlatiladi."
        ),
        "translation": "O'n kun davomida qizarib turadigan gul yo'q.",
        "slot": "kechqurun",
        "reflection": "Sizning bugungi qizarishingiz nimaga sarflanmoqda?",
        "reflection_ko": "오늘 당신의 붉음은 어디에 쓰이고 있나요?",
        "mood": "wilting flower petals falling at sunset, muted warm tones, gentle impermanence",
        "hashtags": ["#otkinchilik", "#mulohaza", "#hayot"],
    },
    {
        "korean": "고생 끝에 낙이 온다",
        "breakdown": [
            ("고생 (gosaeng)", "qiyinchilik, mashaqqat"),
            ("끝에 (kkeute)", "oxirida (에 — o'rin-payt qo'shimchasi)"),
            ("낙 (nak)", "shodlik, rohat (한자어, 樂)"),
            ("이 (i)", "ega qo'shimchasi"),
            ("온다 (onda)", "keladi"),
        ],
        "grammar_note": (
            "에 qo'shimchasi bu yerda vaqt/holat ma'nosida — \"oxirida, "
            "yakunida\" degan bosqichni bildiradi."
        ),
        "translation": "Mashaqqat oxirida shodlik keladi.",
        "slot": "ertalab",
        "reflection": None,
        "mood": "person reaching a mountain summit at sunrise, exhausted but triumphant, golden light breaking through clouds",
        "hashtags": ["#sabr", "#harakat", "#natija"],
    },
    {
        "korean": "티끌 모아 태산",
        "breakdown": [
            ("티끌 (tikkeul)", "chang, mayda zarracha"),
            ("모아 (moa)", "yig'ib (모으다 fe'lining bog'lovchi shakli)"),
            ("태산 (taesan)", "ulkan tog' (한자어, 泰山)"),
        ],
        "grammar_note": (
            "모아 — 모으다 (\"yig'moq\") fe'lining -아/어 bog'lovchi shakli, "
            "harakatni keyingi natija bilan bog'laydi."
        ),
        "translation": "Chang-to'zonlar yig'ilib tog' bo'ladi.",
        "slot": "ertalab",
        "reflection": None,
        "mood": "small pebbles slowly forming a mountain silhouette at dawn, patient accumulation, warm morning light",
        "hashtags": ["#kichikqadamlar", "#sabr", "#izchillik"],
    },
    {
        "korean": "옷깃만 스쳐도 인연이다",
        "breakdown": [
            ("옷깃 (otgit)", "yoqa, kiyim chekkasi"),
            ("만 (man)", "\"hatto/faqat\" ta'kid yuklamasi"),
            ("스쳐도 (seuchyeodo)", "tegib o'tsa ham (스치다 + 아/어도)"),
            ("인연 (inyeon)", "bog'lanish, taqdir aloqasi (한자어, 因緣)"),
            ("이다 (ida)", "\"-dir\" bog'lovchi fe'l"),
        ],
        "grammar_note": (
            "-아/어도 qo'shimchasi \"hatto ... bo'lsa ham\" ma'nosini beradi, "
            "kutilmagan yoki kichik holatning ahamiyatini ta'kidlaydi."
        ),
        "translation": "Yoqa chetigina tegib o'tsa ham, bu bir bog'lanishdir.",
        "slot": "kechqurun",
        "reflection": "Hayotingizga kim yoki nima tasodifan kirib keldi?",
        "reflection_ko": "당신의 삶에 우연히 스며든 사람은 누구인가요?",
        "mood": "two silhouettes passing on a quiet street at dusk, fleeting encounter, warm nostalgic light",
        "hashtags": ["#inson", "#boglanish", "#mulohaza"],
    },
    {
        "korean": "달도 차면 기운다",
        "breakdown": [
            ("달 (dal)", "oy"),
            ("도 (do)", "\"ham\" qo'shimchasi"),
            ("차면 (chamyeon)", "to'lsa (차다 + 면 shart qo'shimchasi)"),
            ("기운다 (giunda)", "egiladi, pasayadi, so'nadi"),
        ],
        "grammar_note": (
            "-면 shart qo'shimchasi \"agar ... bo'lsa\" ma'nosini beradi, ikki "
            "hodisa orasidagi tabiiy bog'liqlikni ko'rsatadi."
        ),
        "translation": "To'lgan oy ham pasayadi.",
        "slot": "kechqurun",
        "reflection": "Hozirgi eng yuqori yoki eng past nuqtangiz sizga nimani his qildirmoqda?",
        "reflection_ko": "지금 당신의 가장 높은 순간, 혹은 가장 낮은 순간은 무엇을 느끼게 하나요?",
        "mood": "full moon fading behind clouds at late evening, cyclical impermanence, deep blue and silver tones",
        "hashtags": ["#hayot", "#ozgarish", "#mulohaza"],
    },
    {
        "korean": "쥐구멍에도 볕 들 날 있다",
        "breakdown": [
            ("쥐구멍 (jwigumeong)", "sichqon teshigi/uyasi"),
            ("에도 (edo)", "\"-da ham\" (o'rin qo'shimchasi + \"ham\")"),
            ("볕 (byeot)", "quyosh nuri"),
            ("들 (deul)", "kiradi (들다 fe'lining negizi)"),
            ("날 (nal)", "kun"),
            ("있다 (itda)", "bor, mavjud"),
        ],
        "grammar_note": (
            "에도 — o'rin kelishigi (에) va \"ham\" yuklamasi (도) birikmasi, "
            "\"hatto shu joyda ham\" ma'nosini kuchaytiradi."
        ),
        "translation": "Sichqon uyasiga ham quyosh nuri kiradigan kun keladi.",
        "slot": "ertalab",
        "reflection": None,
        "mood": "single ray of sunlight breaking through a dark cave opening into vast light, hopeful contrast, dawn",
        "hashtags": ["#umid", "#sabr", "#kunkeladi"],
    },
    {
        "korean": "가는 정이 있어야 오는 정이 있다",
        "breakdown": [
            ("가는 (ganeun)", "ketayotgan (가다 fe'lining sifatdoshi)"),
            ("정 (jeong)", "mehr-oqibat, chin insoniy bog'lanish (한자어, 情)"),
            ("이 (i)", "ega qo'shimchasi"),
            ("있어야 (isseoya)", "bo'lsagina (있다 + -어야 shart qo'shimchasi)"),
            ("오는 (oneun)", "kelayotgan"),
        ],
        "grammar_note": (
            "-어야 qo'shimchasi qattiq shartni bildiradi — \"faqat shunday "
            "bo'lsagina, aks holda yo'q\" degan ma'noni beradi."
        ),
        "translation": "Ketgan mehr bo'lsagina, qaytgan mehr ham bo'ladi.",
        "slot": "ertalab",
        "reflection": None,
        "mood": "two hands offering a warm cup of tea to another person at sunrise, gentle kindness, golden morning light",
        "hashtags": ["#mehr", "#insoniylik", "#harakat"],
    },
    {
        "korean": "아는 길도 물어 가라",
        "breakdown": [
            ("아는 (aneun)", "biladigan (알다 fe'lining sifatdoshi)"),
            ("길 (gil)", "yo'l"),
            ("도 (do)", "\"ham\" qo'shimchasi"),
            ("물어 (mureo)", "so'rab (묻다 fe'lining bog'lovchi shakli)"),
            ("가라 (gara)", "bor (가다 fe'lining buyruq shakli)"),
        ],
        "grammar_note": (
            "-아/어 bog'lovchi shakli ikki harakatni ketma-ket bog'laydi: "
            "\"so'rab, keyin bor\"."
        ),
        "translation": "Bilgan yo'lingizni ham so'rab boring.",
        "slot": "ertalab",
        "reflection": None,
        "mood": "a traveler pausing to check a compass on a familiar sunrise path, quiet humility, warm light",
        "hashtags": ["#kamtarlik", "#ehtiyotkorlik", "#harakat"],
    },
    {
        "korean": "오늘도 수고했어요",
        "breakdown": [
            ("오늘도 (oneuldo)", "bugun ham (오늘 + 도 \"ham\")"),
            ("수고했어요 (sugohaesseoyo)", "mehnat qildingiz, harakat qildingiz (수고하다 fe'lining hurmatli o'tgan zamoni)"),
        ],
        "grammar_note": (
            "-았/었어요 — o'tgan zamon va hurmat darajasini birlashtiruvchi "
            "qo'shimcha, kundalik muloyim nutqda eng ko'p ishlatiladigan shakl."
        ),
        "translation": "Bugun ham o'zingizga mehnatingiz uchun rahmat ayting.",
        "slot": "kechqurun",
        "reflection": "Bugun o'zingizga qanday mehr ko'rsatdingiz?",
        "reflection_ko": "오늘 자신에게 어떤 다정함을 베푸셨나요?",
        "mood": "warm blanket and a cup of tea by a window at night, cozy self-care atmosphere, soft lamp light",
        "hashtags": ["#ozingizgamehr", "#dam", "#minnatdorchilik"],
    },
    {
        "korean": "비 온 뒤에 땅이 굳어진다",
        "breakdown": [
            ("비 (bi)", "yomg'ir"),
            ("온 (on)", "yog'gan (오다 fe'lining o'tgan zamon sifatdoshi)"),
            ("뒤에 (dwie)", "keyin (뒤 \"orqa/keyin\" + 에 o'rin-payt)"),
            ("땅 (ttang)", "yer, tuproq"),
            ("이 (i)", "ega qo'shimchasi"),
            ("굳어진다 (gudeojinda)", "qattiqlashadi, mustahkamlanadi"),
        ],
        "grammar_note": (
            "뒤에 — \"keyin\" ma'nosidagi o'rin-payt birikmasi, bir voqeadan "
            "keyingi holatni bildirish uchun ishlatiladi."
        ),
        "translation": "Yomg'irdan keyin yer yanada mustahkam bo'ladi.",
        "slot": "kechqurun",
        "reflection": "Qiyinchilikdan keyin siz qaysi jihatdan mustahkamlandingiz?",
        "reflection_ko": "어려움을 겪은 뒤, 당신은 어떤 면에서 더 단단해졌나요?",
        "mood": "fresh rain-soaked earth with new green sprouts emerging after a storm, renewal, soft morning light",
        "hashtags": ["#mustahkamlik", "#sabr", "#yangilanish"],
    },
]

def get_random_quote(slot: str) -> dict:
    """Sana asosida navbat bilan tanlaydi - shu sabab ketma-ket ikki kun
    bir xil maqol chiqmaydi. Ro'yxat tugagach, boshidan qayta aylanadi."""
    import datetime
    pool = [q for q in QUOTES if q["slot"] == slot]
    if not pool:
        raise ValueError(f"'{slot}' uchun maqol topilmadi")
    today = datetime.date.today()
    index = today.toordinal() % len(pool)
    return pool[index]
