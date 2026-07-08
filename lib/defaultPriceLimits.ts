import type { PriceLimitMap } from "./types";

// Data bawaan dari PDF batas kewajaran harga per KBLI yang dipakai sebagai patokan validasi.
// Bila referensi harga diperbarui, regenerasi file ini dari PDF/Excel sumber dan deploy ulang aplikasi.
export const DEFAULT_PRICE_LIMITS: PriceLimitMap = {
  "10110": {
    "kbli": "10110",
    "description": "Kegiatan rumah potong dan pengepakan daging bukan unggas",
    "lower": 14000,
    "upper": 140000,
    "sourcePeriod": "1 2025"
  },
  "10120": {
    "kbli": "10120",
    "description": "Kegiatan rumah potong dan pengepakan daging unggas",
    "lower": 22500,
    "upper": 60000,
    "sourcePeriod": "1 2025"
  },
  "10130": {
    "kbli": "10130",
    "description": "Industri pengolahan dan pengawetan produk daging dan daging unggas",
    "lower": 11930,
    "upper": 300000,
    "sourcePeriod": "1 2025"
  },
  "10211": {
    "kbli": "10211",
    "description": "Industri penggaraman/pengeringan ikan",
    "lower": 12000,
    "upper": 660000,
    "sourcePeriod": "1 2025"
  },
  "10212": {
    "kbli": "10212",
    "description": "Industri pengasapan/pemanggangan ikan",
    "lower": 35000,
    "upper": 55000,
    "sourcePeriod": "4 2024"
  },
  "10213": {
    "kbli": "10213",
    "description": "Industri pembekuan ikan",
    "lower": 11000,
    "upper": 526700,
    "sourcePeriod": "1 2025"
  },
  "10214": {
    "kbli": "10214",
    "description": "Industri pemindangan ikan",
    "lower": 13100,
    "upper": 37000,
    "sourcePeriod": "4 2024"
  },
  "10216": {
    "kbli": "10216",
    "description": "Industri berbasis daging lumatan dan surimi",
    "lower": 14000,
    "upper": 85700,
    "sourcePeriod": "1 2025"
  },
  "10219": {
    "kbli": "10219",
    "description": "Industri pengolahan dan pengawetan lainnya untuk ikan",
    "lower": 17900,
    "upper": 23144,
    "sourcePeriod": "4 2024"
  },
  "10221": {
    "kbli": "10221",
    "description": "Industri pengolahan dan pengawetan ikan dan biota air (bukan udang) dalam kaleng",
    "lower": 13000,
    "upper": 950145,
    "sourcePeriod": "1 2025"
  },
  "10222": {
    "kbli": "10222",
    "description": "Industri pengolahan dan pengawetan udang dalam kaleng",
    "lower": 41000,
    "upper": 93000,
    "sourcePeriod": "4 2024"
  },
  "10291": {
    "kbli": "10291",
    "description": "Industri penggaraman/pengeringan biota air lainnya",
    "lower": 120000,
    "upper": 270000,
    "sourcePeriod": "1 2025"
  },
  "10293": {
    "kbli": "10293",
    "description": "Industri pembekuan biota air lainnya",
    "lower": 40000,
    "upper": 293000,
    "sourcePeriod": "1 2025"
  },
  "10298": {
    "kbli": "10298",
    "description": "Industri pengolahan rumput laut",
    "lower": 35000,
    "upper": 250000,
    "sourcePeriod": "1 2025"
  },
  "10299": {
    "kbli": "10299",
    "description": "Industri pengolahan dan pengawetan lainnya untuk biota air lainnya",
    "lower": 25000,
    "upper": 350000,
    "sourcePeriod": "4 2024"
  },
  "10312": {
    "kbli": "10312",
    "description": "Industri pelumatan buah-buahan dan sayuran",
    "lower": 12900,
    "upper": 83000,
    "sourcePeriod": "1 2025"
  },
  "10313": {
    "kbli": "10313",
    "description": "Industri pengeringan buah-buahan dan sayuran",
    "lower": 17000,
    "upper": 120000,
    "sourcePeriod": "1 2025"
  },
  "10314": {
    "kbli": "10314",
    "description": "Industri pembekuan buah-buahan dan sayuran",
    "lower": 17813,
    "upper": 76000,
    "sourcePeriod": "4 2024"
  },
  "10330": {
    "kbli": "10330",
    "description": "Industri pengolahan sari buah dan sayuran",
    "lower": 0,
    "upper": 2350,
    "sourcePeriod": "1 2025"
  },
  "10391": {
    "kbli": "10391",
    "description": "Industri tempe kedelai",
    "lower": 11600,
    "upper": 22000,
    "sourcePeriod": "1 2025"
  },
  "10392": {
    "kbli": "10392",
    "description": "Industri tahu kedelai",
    "lower": 10606,
    "upper": 120000,
    "sourcePeriod": "1 2025"
  },
  "10411": {
    "kbli": "10411",
    "description": "Industri minyak mentah dan lemak nabati",
    "lower": 1894635,
    "upper": 1994635,
    "sourcePeriod": "3 2024"
  },
  "10414": {
    "kbli": "10414",
    "description": "Industri minyak ikan",
    "lower": 13404,
    "upper": 18180,
    "sourcePeriod": "4 2024"
  },
  "10421": {
    "kbli": "10421",
    "description": "Industri kopra",
    "lower": 11000,
    "upper": 20700,
    "sourcePeriod": "1 2025"
  },
  "10422": {
    "kbli": "10422",
    "description": "Industri minyak mentah kelapa",
    "lower": 11200,
    "upper": 25000,
    "sourcePeriod": "1 2025"
  },
  "10423": {
    "kbli": "10423",
    "description": "Industri minyak goreng kelapa",
    "lower": 21000,
    "upper": 35150,
    "sourcePeriod": "1 2025"
  },
  "10431": {
    "kbli": "10431",
    "description": "Industri minyak mentah kelapa sawit (crude palm oil)",
    "lower": 11000,
    "upper": 16522,
    "sourcePeriod": "1 2025"
  },
  "10432": {
    "kbli": "10432",
    "description": "Industri minyak mentah inti kelapa sawit (crude palm kernel oil)",
    "lower": 10020,
    "upper": 22262,
    "sourcePeriod": "1 2025"
  },
  "10433": {
    "kbli": "10433",
    "description": "Industri pemisahan/fraksinasi minyak mentah kelapa sawit dan minyak mentah inti",
    "lower": 10462,
    "upper": 11918,
    "sourcePeriod": "1 2025"
  },
  "10434": {
    "kbli": "10434",
    "description": "Industri pemurnian minyak mentah kelapa sawit dan minyak mentah inti kelapa sawit",
    "lower": 10073,
    "upper": 11327,
    "sourcePeriod": "3 2024"
  },
  "10435": {
    "kbli": "10435",
    "description": "Industri pemisahan/fraksinasi minyak murni kelapa sawit",
    "lower": 13313,
    "upper": 14895,
    "sourcePeriod": "1 2025"
  },
  "10437": {
    "kbli": "10437",
    "description": "Industri minyak goreng kelapa sawit",
    "lower": 13413,
    "upper": 17939,
    "sourcePeriod": "1 2025"
  },
  "10590": {
    "kbli": "10590",
    "description": "Industri pengolahan produk dari susu lainnya",
    "lower": 35742,
    "upper": 80000,
    "sourcePeriod": "1 2025"
  },
  "10611": {
    "kbli": "10611",
    "description": "Industri penggilingan gandum dan serelia lainnya",
    "lower": 0,
    "upper": 3880,
    "sourcePeriod": "4 2024"
  },
  "10613": {
    "kbli": "10613",
    "description": "Industri penggilingan aneka umbi dan sayuran (termasuk rhizoma)",
    "lower": 0,
    "upper": 7000,
    "sourcePeriod": "4 2024"
  },
  "10616": {
    "kbli": "10616",
    "description": "Industri tepung terigu",
    "lower": 0,
    "upper": 7122,
    "sourcePeriod": "4 2024"
  },
  "10621": {
    "kbli": "10621",
    "description": "Industri pati ubi kayu",
    "lower": 0,
    "upper": 10000,
    "sourcePeriod": "1 2025"
  },
  "10622": {
    "kbli": "10622",
    "description": "Industri berbagai macam pati palma",
    "lower": 18000,
    "upper": 32000,
    "sourcePeriod": "4 2024"
  },
  "10623": {
    "kbli": "10623",
    "description": "Industri glukosa dan sejenisnya",
    "lower": 0,
    "upper": 8260,
    "sourcePeriod": "4 2024"
  },
  "10631": {
    "kbli": "10631",
    "description": "Industri penggilingan padi dan penyosohan beras",
    "lower": 10600,
    "upper": 15000,
    "sourcePeriod": "1 2025"
  },
  "10632": {
    "kbli": "10632",
    "description": "Industri penggilingan dan pembersihan jagung",
    "lower": 0,
    "upper": 7100,
    "sourcePeriod": "4 2024"
  },
  "10633": {
    "kbli": "10633",
    "description": "Industri tepung beras dan tepung jagung",
    "lower": 10261,
    "upper": 12000,
    "sourcePeriod": "3 2024"
  },
  "10710": {
    "kbli": "10710",
    "description": "Industri produk roti dan kue",
    "lower": 17000,
    "upper": 250000,
    "sourcePeriod": "1 2025"
  },
  "10721": {
    "kbli": "10721",
    "description": "Industri gula pasir",
    "lower": 14500,
    "upper": 15500,
    "sourcePeriod": "1 2025"
  },
  "10722": {
    "kbli": "10722",
    "description": "Industri gula merah",
    "lower": 11000,
    "upper": 79365,
    "sourcePeriod": "1 2025"
  },
  "10729": {
    "kbli": "10729",
    "description": "Industri pengolahan gula lainnya bukan sirop",
    "lower": 16300,
    "upper": 35200,
    "sourcePeriod": "4 2024"
  },
  "10731": {
    "kbli": "10731",
    "description": "Industri kakao",
    "lower": 38000,
    "upper": 250000,
    "sourcePeriod": "1 2025"
  },
  "10732": {
    "kbli": "10732",
    "description": "Industri makanan dari cokelat dan kembang gula dari coklat",
    "lower": 30000,
    "upper": 466000,
    "sourcePeriod": "1 2025"
  },
  "10733": {
    "kbli": "10733",
    "description": "Industri manisan buah-buahan dan sayuran kering",
    "lower": 60000,
    "upper": 80000,
    "sourcePeriod": "1 2025"
  },
  "10734": {
    "kbli": "10734",
    "description": "Industri kembang gula",
    "lower": 26000,
    "upper": 126199,
    "sourcePeriod": "1 2025"
  },
  "10739": {
    "kbli": "10739",
    "description": "Industri kembang gula lainnya",
    "lower": 123811,
    "upper": 125132,
    "sourcePeriod": "4 2024"
  },
  "10740": {
    "kbli": "10740",
    "description": "Industri makaroni, mie dan produk sejenisnya",
    "lower": 14000,
    "upper": 118000,
    "sourcePeriod": "1 2025"
  },
  "10750": {
    "kbli": "10750",
    "description": "Industri makanan dan masakan olahan",
    "lower": 36000,
    "upper": 246380,
    "sourcePeriod": "1 2025"
  },
  "10761": {
    "kbli": "10761",
    "description": "Industri pengolahan kopi",
    "lower": 11205,
    "upper": 300000,
    "sourcePeriod": "1 2025"
  },
  "10763": {
    "kbli": "10763",
    "description": "Industri pengolahan teh",
    "lower": 12500,
    "upper": 463626,
    "sourcePeriod": "1 2025"
  },
  "10771": {
    "kbli": "10771",
    "description": "Industri kecap",
    "lower": 14000,
    "upper": 24000,
    "sourcePeriod": "4 2024"
  },
  "10772": {
    "kbli": "10772",
    "description": "Industri bumbu masak dan penyedap masakan",
    "lower": 12765,
    "upper": 800000,
    "sourcePeriod": "1 2025"
  },
  "10773": {
    "kbli": "10773",
    "description": "Industri produk masak dari kelapa",
    "lower": 14000,
    "upper": 46800,
    "sourcePeriod": "1 2025"
  },
  "10774": {
    "kbli": "10774",
    "description": "Industri pengolahan garam",
    "lower": 0,
    "upper": 27000,
    "sourcePeriod": "1 2025"
  },
  "10779": {
    "kbli": "10779",
    "description": "Industri produk masak lainnya",
    "lower": 30000,
    "upper": 40000,
    "sourcePeriod": "1 2025"
  },
  "10792": {
    "kbli": "10792",
    "description": "Industri kue basah",
    "lower": 16000,
    "upper": 58000,
    "sourcePeriod": "4 2024"
  },
  "10793": {
    "kbli": "10793",
    "description": "Industri makanan dari kedele dan kacang-kacangan lainnya bukan kecap, tempe dan",
    "lower": 15000,
    "upper": 220000,
    "sourcePeriod": "1 2025"
  },
  "10794": {
    "kbli": "10794",
    "description": "Industri kerupuk, keripik, peyek dan sejenisnya",
    "lower": 12078,
    "upper": 210000,
    "sourcePeriod": "1 2025"
  },
  "10796": {
    "kbli": "10796",
    "description": "Industri dodol",
    "lower": 16000,
    "upper": 80000,
    "sourcePeriod": "1 2025"
  },
  "10801": {
    "kbli": "10801",
    "description": "Industri ransum makanan hewan",
    "lower": 14293,
    "upper": 14939,
    "sourcePeriod": "1 2025"
  },
  "10802": {
    "kbli": "10802",
    "description": "Industri konsentrat makanan hewan",
    "lower": 10817,
    "upper": 18000,
    "sourcePeriod": "4 2024"
  },
  "11040": {
    "kbli": "11040",
    "description": "Industri minuman ringan",
    "lower": 63000,
    "upper": 65000,
    "sourcePeriod": "1 2025"
  },
  "12011": {
    "kbli": "12011",
    "description": "Industri sigaret kretek tangan",
    "lower": 90000,
    "upper": 142857,
    "sourcePeriod": "1 2025"
  },
  "12091": {
    "kbli": "12091",
    "description": "Industri pengeringan dan pengolahan tembakau",
    "lower": 12000,
    "upper": 844750,
    "sourcePeriod": "1 2025"
  },
  "12099": {
    "kbli": "12099",
    "description": "Industri bumbu rokok serta kelengkapan rokok lainnya",
    "lower": 28500,
    "upper": 127000,
    "sourcePeriod": "1 2025"
  },
  "13112": {
    "kbli": "13112",
    "description": "Industri pemintalan benang",
    "lower": 23315,
    "upper": 138000,
    "sourcePeriod": "1 2025"
  },
  "13113": {
    "kbli": "13113",
    "description": "Industri pemintalan benang jahit",
    "lower": 18725,
    "upper": 136029,
    "sourcePeriod": "1 2025"
  },
  "13121": {
    "kbli": "13121",
    "description": "Industri pertenunan (bukan pertenunan karung goni dan karung lainnya)",
    "lower": 70000,
    "upper": 98000,
    "sourcePeriod": "4 2024"
  },
  "13122": {
    "kbli": "13122",
    "description": "Industri kain tenun ikat",
    "lower": 30000,
    "upper": 63000,
    "sourcePeriod": "1 2025"
  },
  "13131": {
    "kbli": "13131",
    "description": "Industri penyempurnaan benang",
    "lower": 44300,
    "upper": 86300,
    "sourcePeriod": "4 2024"
  },
  "13132": {
    "kbli": "13132",
    "description": "Industri penyempurnaan kain",
    "lower": 10314,
    "upper": 12099,
    "sourcePeriod": "4 2024"
  },
  "13133": {
    "kbli": "13133",
    "description": "Industri pencetakan kain",
    "lower": 88000,
    "upper": 101000,
    "sourcePeriod": "1 2025"
  },
  "13911": {
    "kbli": "13911",
    "description": "Industri kain rajutan",
    "lower": 24000,
    "upper": 72000,
    "sourcePeriod": "1 2025"
  },
  "13941": {
    "kbli": "13941",
    "description": "Industri tali",
    "lower": 11000,
    "upper": 125000,
    "sourcePeriod": "1 2025"
  },
  "13942": {
    "kbli": "13942",
    "description": "Industri barang dari tali",
    "lower": 42300,
    "upper": 125000,
    "sourcePeriod": "1 2025"
  },
  "13991": {
    "kbli": "13991",
    "description": "Industri kain pita (narrow fabric)",
    "lower": 0,
    "upper": 658,
    "sourcePeriod": "3 2024"
  },
  "13992": {
    "kbli": "13992",
    "description": "Industri yang menghasilkan kain keperluan industri",
    "lower": 25000,
    "upper": 800000,
    "sourcePeriod": "1 2025"
  },
  "13993": {
    "kbli": "13993",
    "description": "Industri non woven (bukan tenunan)",
    "lower": 16027,
    "upper": 25437,
    "sourcePeriod": "1 2025"
  },
  "13995": {
    "kbli": "13995",
    "description": "Industri kapuk",
    "lower": 13000,
    "upper": 17000,
    "sourcePeriod": "3 2024"
  },
  "14111": {
    "kbli": "14111",
    "description": "Industri pakaian jadi (konveksi) dari tekstil",
    "lower": 88000,
    "upper": 224000,
    "sourcePeriod": "4 2024"
  },
  "15112": {
    "kbli": "15112",
    "description": "Industri penyamakan kulit",
    "lower": 23000,
    "upper": 38000,
    "sourcePeriod": "1 2025"
  },
  "16104": {
    "kbli": "16104",
    "description": "Industri pengolahan rotan",
    "lower": 11000,
    "upper": 22000,
    "sourcePeriod": "1 2025"
  },
  "16299": {
    "kbli": "16299",
    "description": "Industri barang dari kayu, rotan, gabus lainnya ytdl",
    "lower": 12000,
    "upper": 23000,
    "sourcePeriod": "1 2025"
  },
  "17021": {
    "kbli": "17021",
    "description": "Industri kertas dan papan kertas bergelombang",
    "lower": 11210,
    "upper": 25000,
    "sourcePeriod": "1 2025"
  },
  "17022": {
    "kbli": "17022",
    "description": "Industri kemasan dan kotak dari kertas dan karton",
    "lower": 11500,
    "upper": 31287,
    "sourcePeriod": "1 2025"
  },
  "17091": {
    "kbli": "17091",
    "description": "Industri kertas tissue",
    "lower": 10879,
    "upper": 14958,
    "sourcePeriod": "1 2025"
  },
  "17099": {
    "kbli": "17099",
    "description": "Industri barang dari kertas dan papan kertas lainnya ytdl",
    "lower": 0,
    "upper": 3700,
    "sourcePeriod": "4 2024"
  },
  "18111": {
    "kbli": "18111",
    "description": "Industri pencetakan umum",
    "lower": 20000,
    "upper": 89600,
    "sourcePeriod": "1 2025"
  },
  "19100": {
    "kbli": "19100",
    "description": "Industri produk dari batu bara",
    "lower": 0,
    "upper": 1454,
    "sourcePeriod": "1 2025"
  },
  "19212": {
    "kbli": "19212",
    "description": "Industri pembuatan minyak pelumas",
    "lower": 14160,
    "upper": 3665750,
    "sourcePeriod": "1 2025"
  },
  "19291": {
    "kbli": "19291",
    "description": "Industri produk dari hasil kilang minyak bumi",
    "lower": 10583,
    "upper": 12000,
    "sourcePeriod": "1 2025"
  },
  "19292": {
    "kbli": "19292",
    "description": "Industri briket batu bara",
    "lower": 18700,
    "upper": 19000,
    "sourcePeriod": "4 2024"
  },
  "20111": {
    "kbli": "20111",
    "description": "Industri kimia dasar anorganik khlor dan alkali",
    "lower": 24043,
    "upper": 53975,
    "sourcePeriod": "4 2024"
  },
  "20112": {
    "kbli": "20112",
    "description": "Industri kimia dasar anorganik gas industri",
    "lower": 9929,
    "upper": 138960,
    "sourcePeriod": "1 2025"
  },
  "20113": {
    "kbli": "20113",
    "description": "Industri kimia dasar anorganik pigmen",
    "lower": 20000,
    "upper": 1183000,
    "sourcePeriod": "4 2024"
  },
  "20114": {
    "kbli": "20114",
    "description": "Industri kimia dasar anorganik lainnya",
    "lower": 21713,
    "upper": 78480,
    "sourcePeriod": "1 2025"
  },
  "20115": {
    "kbli": "20115",
    "description": "Industri kimia dasar organik yang bersumber dari hasil pertanian",
    "lower": 11000,
    "upper": 28491906,
    "sourcePeriod": "1 2025"
  },
  "20116": {
    "kbli": "20116",
    "description": "Industri kimia dasar organik untuk bahan baku zat warna dan pigmen, zat warna dan",
    "lower": 39474,
    "upper": 172000,
    "sourcePeriod": "1 2025"
  },
  "20117": {
    "kbli": "20117",
    "description": "Industri kimia dasar organik yang bersumber dari minyak bumi, gas alam dan batu bara",
    "lower": 18500,
    "upper": 24500,
    "sourcePeriod": "3 2024"
  },
  "20118": {
    "kbli": "20118",
    "description": "Industri kimia dasar organik yang menghasilkan bahan kimia khusus",
    "lower": 12275,
    "upper": 223000,
    "sourcePeriod": "1 2025"
  },
  "20121": {
    "kbli": "20121",
    "description": "Industri pupuk alam/non sintetis hara makro primer",
    "lower": 10820,
    "upper": 155000,
    "sourcePeriod": "1 2025"
  },
  "20122": {
    "kbli": "20122",
    "description": "Industri pupuk buatan tunggal hara makro primer",
    "lower": 14430,
    "upper": 15000,
    "sourcePeriod": "4 2024"
  },
  "20123": {
    "kbli": "20123",
    "description": "Industri pupuk buatan majemuk hara makro primer",
    "lower": 15000,
    "upper": 16095,
    "sourcePeriod": "1 2025"
  },
  "20124": {
    "kbli": "20124",
    "description": "Industri pupuk buatan campuran hara makro primer",
    "lower": 0,
    "upper": 4320,
    "sourcePeriod": "4 2024"
  },
  "20127": {
    "kbli": "20127",
    "description": "Industri pupuk pelengkap",
    "lower": 0,
    "upper": 2386,
    "sourcePeriod": "4 2024"
  },
  "20131": {
    "kbli": "20131",
    "description": "Industri damar buatan (resin sintetis) dan bahan baku plastik",
    "lower": 10991,
    "upper": 34000,
    "sourcePeriod": "1 2025"
  },
  "20212": {
    "kbli": "20212",
    "description": "Industri pemberantas hama (formulasi)",
    "lower": 50000,
    "upper": 170000,
    "sourcePeriod": "4 2024"
  },
  "20214": {
    "kbli": "20214",
    "description": "Industri bahan amelioran (pembenah tanah)",
    "lower": 0,
    "upper": 6306,
    "sourcePeriod": "1 2025"
  },
  "20221": {
    "kbli": "20221",
    "description": "Industri cat dan tinta cetak",
    "lower": 12500,
    "upper": 534000,
    "sourcePeriod": "1 2025"
  },
  "20223": {
    "kbli": "20223",
    "description": "Industri lak",
    "lower": 10500,
    "upper": 20370,
    "sourcePeriod": "4 2024"
  },
  "20231": {
    "kbli": "20231",
    "description": "Industri sabun dan bahan pembersih keperluan rumah tangga",
    "lower": 12532,
    "upper": 45000,
    "sourcePeriod": "1 2025"
  },
  "20232": {
    "kbli": "20232",
    "description": "Industri kosmetik untuk manusia, termasuk pasta gigi",
    "lower": 24921,
    "upper": 400000,
    "sourcePeriod": "1 2025"
  },
  "20291": {
    "kbli": "20291",
    "description": "Industri perekat/lem",
    "lower": 13712,
    "upper": 95500,
    "sourcePeriod": "1 2025"
  },
  "20293": {
    "kbli": "20293",
    "description": "Industri tinta",
    "lower": 80000,
    "upper": 96500,
    "sourcePeriod": "4 2024"
  },
  "20294": {
    "kbli": "20294",
    "description": "Industri minyak atsiri",
    "lower": 127500,
    "upper": 2557152,
    "sourcePeriod": "1 2025"
  },
  "21012": {
    "kbli": "21012",
    "description": "Industri produk farmasi untuk manusia",
    "lower": 29350,
    "upper": 1555533,
    "sourcePeriod": "4 2024"
  },
  "21013": {
    "kbli": "21013",
    "description": "Industri produk farmasi untuk hewan",
    "lower": 11645,
    "upper": 250000,
    "sourcePeriod": "1 2025"
  },
  "21022": {
    "kbli": "21022",
    "description": "Industri produk obat tradisional untuk manusia",
    "lower": 20000,
    "upper": 90000,
    "sourcePeriod": "1 2025"
  },
  "22112": {
    "kbli": "22112",
    "description": "Industri vulkanisir ban",
    "lower": 22400,
    "upper": 40000,
    "sourcePeriod": "4 2024"
  },
  "22121": {
    "kbli": "22121",
    "description": "Industri pengasapan karet",
    "lower": 23200,
    "upper": 44166,
    "sourcePeriod": "1 2025"
  },
  "22122": {
    "kbli": "22122",
    "description": "Industri remilling karet",
    "lower": 10500,
    "upper": 38000,
    "sourcePeriod": "1 2025"
  },
  "22123": {
    "kbli": "22123",
    "description": "Industri karet remah (crumb rubber)",
    "lower": 13500,
    "upper": 90000,
    "sourcePeriod": "1 2025"
  },
  "22191": {
    "kbli": "22191",
    "description": "Industri barang dari karet untuk keperluan rumah tangga",
    "lower": 18000,
    "upper": 45000,
    "sourcePeriod": "1 2025"
  },
  "22192": {
    "kbli": "22192",
    "description": "Industri barang dari karet untuk keperluan industri",
    "lower": 19000,
    "upper": 496171,
    "sourcePeriod": "1 2025"
  },
  "22199": {
    "kbli": "22199",
    "description": "Industri barang dari karet lainnya ytdl",
    "lower": 23400,
    "upper": 40000,
    "sourcePeriod": "4 2024"
  },
  "22220": {
    "kbli": "22220",
    "description": "Industri barang dari plastik untuk pengemasan",
    "lower": 11375,
    "upper": 119637,
    "sourcePeriod": "1 2025"
  },
  "22230": {
    "kbli": "22230",
    "description": "Industri pipa plastik dan perlengkapannya",
    "lower": 16793,
    "upper": 56000,
    "sourcePeriod": "1 2025"
  },
  "22291": {
    "kbli": "22291",
    "description": "Industri barang plastik lembaran",
    "lower": 10580,
    "upper": 58930,
    "sourcePeriod": "1 2025"
  },
  "22292": {
    "kbli": "22292",
    "description": "Industri perlengkapan dan peralatan rumah tangga (tidak termasuk furnitur)",
    "lower": 24000,
    "upper": 65000,
    "sourcePeriod": "1 2025"
  },
  "22299": {
    "kbli": "22299",
    "description": "Industri barang plastik lainnya ytdl",
    "lower": 10525,
    "upper": 32000,
    "sourcePeriod": "1 2025"
  },
  "23121": {
    "kbli": "23121",
    "description": "Industri perlengkapan dan peralatan rumah tangga dari kaca",
    "lower": 15868,
    "upper": 34225,
    "sourcePeriod": "4 2024"
  },
  "23939": {
    "kbli": "23939",
    "description": "Industri barang tanah liat/keramik dan porselen lainnya bukan bahan bangunan",
    "lower": 0,
    "upper": 2747,
    "sourcePeriod": "4 2024"
  },
  "23942": {
    "kbli": "23942",
    "description": "Industri kapur",
    "lower": 133750,
    "upper": 220000,
    "sourcePeriod": "4 2024"
  },
  "23952": {
    "kbli": "23952",
    "description": "Industri barang dari kapur",
    "lower": 0,
    "upper": 538,
    "sourcePeriod": "4 2024"
  },
  "23957": {
    "kbli": "23957",
    "description": "Industri mortar atau beton siap pakai",
    "lower": 55000,
    "upper": 96000,
    "sourcePeriod": "1 2025"
  },
  "24101": {
    "kbli": "24101",
    "description": "Industri besi dan baja dasar (iron and steel making)",
    "lower": 11844,
    "upper": 167900,
    "sourcePeriod": "1 2025"
  },
  "24102": {
    "kbli": "24102",
    "description": "Industri penggilingan baja (steel rolling)",
    "lower": 14100,
    "upper": 15560000,
    "sourcePeriod": "1 2025"
  },
  "24103": {
    "kbli": "24103",
    "description": "Industri pipa dan sambungan pipa dari baja dan besi",
    "lower": 47286,
    "upper": 69434,
    "sourcePeriod": "1 2025"
  },
  "24201": {
    "kbli": "24201",
    "description": "Industri pembuatan logam dasar mulia",
    "lower": 11000000,
    "upper": 1534000000,
    "sourcePeriod": "1 2025"
  },
  "24202": {
    "kbli": "24202",
    "description": "Industri pembuatan logam dasar bukan besi",
    "lower": 18000,
    "upper": 420000,
    "sourcePeriod": "1 2025"
  },
  "24203": {
    "kbli": "24203",
    "description": "Industri penggilingan logam bukan besi",
    "lower": 0,
    "upper": 6728,
    "sourcePeriod": "4 2024"
  },
  "24310": {
    "kbli": "24310",
    "description": "Industri pengecoran besi dan baja",
    "lower": 14500,
    "upper": 444928,
    "sourcePeriod": "1 2025"
  },
  "24320": {
    "kbli": "24320",
    "description": "Industri pengecoran logam bukan besi dan baja",
    "lower": 32000,
    "upper": 38000,
    "sourcePeriod": "4 2024"
  },
  "25111": {
    "kbli": "25111",
    "description": "Industri barang dari logam bukan aluminium siap pasang untuk bangunan",
    "lower": 14414,
    "upper": 3693634,
    "sourcePeriod": "1 2025"
  },
  "25112": {
    "kbli": "25112",
    "description": "Industri barang dari logam aluminium siap pasang untuk bangunan",
    "lower": 52000,
    "upper": 60500,
    "sourcePeriod": "4 2024"
  },
  "25119": {
    "kbli": "25119",
    "description": "Industri barang dari logam siap pasang untuk konstruksi lainnya",
    "lower": 19100,
    "upper": 19250,
    "sourcePeriod": "1 2025"
  },
  "25951": {
    "kbli": "25951",
    "description": "Industri barang dari kawat",
    "lower": 12000,
    "upper": 160000,
    "sourcePeriod": "1 2025"
  },
  "25952": {
    "kbli": "25952",
    "description": "Industri paku, mur dan baut",
    "lower": 10291,
    "upper": 25000,
    "sourcePeriod": "1 2025"
  },
  "25992": {
    "kbli": "25992",
    "description": "Industri peralatan dapur dan peralatan meja dari logam",
    "lower": 39200,
    "upper": 52500,
    "sourcePeriod": "4 2024"
  },
  "25999": {
    "kbli": "25999",
    "description": "Industri barang logam lainnya ytdl",
    "lower": 11660,
    "upper": 17800,
    "sourcePeriod": "4 2024"
  },
  "27320": {
    "kbli": "27320",
    "description": "Industri kabel listrik dan elektronik lainnya",
    "lower": 11000,
    "upper": 101700,
    "sourcePeriod": "1 2025"
  },
  "30912": {
    "kbli": "30912",
    "description": "Industri komponen dan perlengkapan sepeda motor roda dua dan tiga",
    "lower": 11000,
    "upper": 91141,
    "sourcePeriod": "4 2024"
  },
  "32112": {
    "kbli": "32112",
    "description": "Industri barang perhiasan dari logam mulia untuk keperluan pribadi",
    "lower": 734000000,
    "upper": 812000000,
    "sourcePeriod": "4 2024"
  },
  "32300": {
    "kbli": "32300",
    "description": "Industri alat olahraga",
    "lower": 35000,
    "upper": 75000,
    "sourcePeriod": "1 2025"
  },
  "32401": {
    "kbli": "32401",
    "description": "Industri alat permainan",
    "lower": 19315,
    "upper": 32500,
    "sourcePeriod": "4 2024"
  },
  "32901": {
    "kbli": "32901",
    "description": "Industri alat tulis dan gambar termasuk perlengkapannya",
    "lower": 46500,
    "upper": 49900,
    "sourcePeriod": "1 2025"
  },
  "32903": {
    "kbli": "32903",
    "description": "Industri kerajinan ytdl",
    "lower": 250000,
    "upper": 325000,
    "sourcePeriod": "1 2025"
  },
  "32909": {
    "kbli": "32909",
    "description": "Industri pengolahan lainnya ytdl",
    "lower": 245000,
    "upper": 682362,
    "sourcePeriod": "4 2024"
  }
};
