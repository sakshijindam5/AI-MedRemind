"""
Disease Information and Multilingual Treatment Service
Includes database initial seeder with verified Marathi, Hindi, and English advice.
"""

from sqlalchemy.orm import Session
from app.models import Disease, Treatment

# Verified agronomic knowledgebase for our 12 classes
INITIAL_CROP_KNOWLEDGE = [
    {
        "crop": "Tomato",
        "class_name": "Tomato___Early_blight",
        "name_en": "Tomato Early Blight",
        "name_mr": "टोमॅटोवरील अगेती करपा (Early Blight)",
        "name_hi": "टमाटर का अगेती झुलसा",
        "is_healthy": False,
        "organic_mr": "१०% गोमूत्र किंवा निंबोळी अर्क (५%) फवारा. ट्रायकोडर्मा व्हिरिडी ५ ग्रॅम/लिटर पाण्यात मिसळून पानांवर फवारणी करा.",
        "organic_hi": "नीम का तेल (5 मि.ली./लीटर) या ट्राइकोडर्मा विरिडी (5 ग्राम/लीटर) पानी में मिलाकर छिड़काव करें।",
        "organic_en": "Spray Neem seed kernel extract (5%) or Trichoderma viride at 5g per litre of water.",
        "chemical_mr": "मँकोझेब (Mancozeb 75% WP) २.५ ग्रॅम किंवा कॉपर ऑक्सिक्लोराईड ३ ग्रॅम प्रति लिटर पाण्यात मिसळून फवारा.",
        "chemical_hi": "मैंकोजेब 75% WP (2.5 ग्राम/लीटर) या कॉपर ऑक्सीक्लोराइड (3 ग्राम/लीटर) पानी में मिलाकर छिड़कें।",
        "chemical_en": "Spray Mancozeb 75% WP @ 2.5g/L or Copper Oxychloride 50% WP @ 3g/L water.",
        "preventive_mr": "पिकांची फेरपालट करा. झाडांच्या बुंध्याशी पाण्याचा निचरा व्यवस्थित ठेवा आणि जुनी बाधित पाने नष्ट करा.",
        "preventive_hi": "फसल चक्र अपनाएं। जल निकासी अच्छी रखें और रोगग्रस्त पत्तों को खेत से हटाकर नष्ट करें।",
        "preventive_en": "Follow crop rotation. Ensure proper drainage and burn/remove heavily infected bottom leaves."
    },
    {
        "crop": "Tomato",
        "class_name": "Tomato___Late_blight",
        "name_en": "Tomato Late Blight",
        "name_mr": "टोमॅटोवरील पछेती करपा (Late Blight)",
        "name_hi": "टमाटर का पछेती झुलसा",
        "is_healthy": False,
        "organic_mr": "ताक आणि हिंगाचे द्रावण (५ लिटर ताक + ५० ग्रॅम हिंग १०० लिटर पाण्यात) फवारा. बोर्डो मिश्रण १% फवारा.",
        "organic_hi": "बोर्डो मिश्रण 1% का छिड़काव करें। छाछ और हींग का घोल बनाकर छिड़कें।",
        "organic_en": "Spray 1% Bordeaux mixture. Use sour buttermilk spray with asafoetida.",
        "chemical_mr": "रिडोमील गोल्ड (Metalaxyl + Mancozeb) २ ग्रॅम/लिटर किंवा सायमोक्सॅनिल + मँकोझेब २.५ ग्रॅम/लिटर फवारा.",
        "chemical_hi": "रिडोमिल गोल्ड (2 ग्राम/लीटर) या साइमोक्सानिल + मैंकोजेब का 10-12 दिन के अंतराल पर छिड़काव करें।",
        "chemical_en": "Spray Metalaxyl + Mancozeb (Ridomil Gold) @ 2g/L or Cymoxanil + Mancozeb @ 2.5g/L.",
        "preventive_mr": "ढगाळ व थंड दमट हवामानात त्वरित फवारणी करा. ठिबक सिंचनाचा वापर करा जेणेकरून पाने ओली राहणार नाहीत.",
        "preventive_hi": "बादल वाले और नम मौसम में तुरंत निगरानी रखें। पत्तियों पर ऊपर से पानी न डालें।",
        "preventive_en": "Avoid sprinkler irrigation to prevent leaf wetness. Monitor closely during cloudy, humid weather."
    },
    {
        "crop": "Tomato",
        "class_name": "Tomato___Leaf_Mold",
        "name_en": "Tomato Leaf Mold",
        "name_mr": "टोमॅटोवरील पानांवरील बुरशी (Leaf Mold)",
        "name_hi": "टमाटर की पत्ती का फफूंद रोग",
        "is_healthy": False,
        "organic_mr": "बेकिंग सोडा (३ ग्रॅम/लिटर) साबणाच्या पाण्यासोबत मिसळून फवारा. ट्रायकोडर्माचा वापर करा.",
        "organic_hi": "बेकिंग सोडा (3 ग्राम/लीटर) हल्के साबुन के पानी में मिलाकर छिड़कें।",
        "organic_en": "Spray potassium bicarbonate or baking soda (3g/L) with mild organic soap.",
        "chemical_mr": "क्लोरोथॅलोनिल (Chlorothalonil) २ ग्रॅम/लिटर किंवा कार्बेन्डाझिम १ ग्रॅम प्रति लिटर पाण्यात फवारा.",
        "chemical_hi": "कार्बेंडाजिम 50% WP (1 ग्राम/लीटर) या क्लोरोथालोनिल (2 ग्राम/लीटर) का छिड़काव करें।",
        "chemical_en": "Spray Chlorothalonil @ 2g/L or Carbendazim 50% WP @ 1g/L of water.",
        "preventive_mr": "झाडांमध्ये हवा खेळती राहण्यासाठी योग्य अंतर ठेवा आणि खालील जुनी पाने छाटा.",
        "preventive_hi": "पौधों के बीच हवा का संचार अच्छा रखें और निचली पत्तियां हटा दें।",
        "preventive_en": "Improve ventilation around plants by pruning dense foliage."
    },
    {
        "crop": "Tomato",
        "class_name": "Tomato___Yellow_Leaf_Curl_Virus",
        "name_en": "Tomato Yellow Leaf Curl Virus",
        "name_mr": "टोमॅटो पर्णगुच्छ / पिवळा विषाणू (Churda-Murda)",
        "name_hi": "टमाटर का पीला पत्ता मरोड़िया रोग",
        "is_healthy": False,
        "organic_mr": "पिवळे चिकट सापळे (Yellow Sticky Traps) एकरी २० लावा. ५% निंबोळी तेलाची फवारणी करून पांढरी माशी नियंत्रित करा.",
        "organic_hi": "प्रति एकड़ 20 पीले चिपचिपे जाल लगाएं। सफेद मक्खी नियंत्रण के लिए 5% नीम तेल छिड़कें।",
        "organic_en": "Install 20 yellow sticky traps per acre. Spray 5% Neem oil to control whitefly vector.",
        "chemical_mr": "व्हायरस वाहक पांढऱ्या माशीसाठी डायमेथोएट ३०% EC १.५ मिली किंवा इमिडाक्लोप्रिड ०.३ मिली प्रति लिटर फवारा.",
        "chemical_hi": "सफेद मक्खी के लिए इमिडाक्लोप्रिड 17.8% SL (0.3 मिली/लीटर) या एसिटामिप्रिड छिड़कें।",
        "chemical_en": "Spray Imidacloprid 17.8% SL @ 0.3ml/L or Acetamiprid 20% SP @ 0.4g/L to control whiteflies.",
        "preventive_mr": "हा विषाणू पांढऱ्या माशीमुळे पसरतो. बाधित झालेली झाडे मुळासकट उपटून शेताबाहेर नष्ट करा.",
        "preventive_hi": "रोगग्रस्त पौधों को तुरंत उखाड़कर नष्ट करें। सफेद मक्खी को खेत में न पनपने दें।",
        "preventive_en": "Rogue out infected stunted plants. Control whitefly population early in seedling stage."
    },
    {
        "crop": "Tomato",
        "class_name": "Tomato___Healthy",
        "name_en": "Healthy Tomato",
        "name_mr": "निरोगी टोमॅटो पीक",
        "name_hi": "स्वस्थ टमाटर का पौधा",
        "is_healthy": True,
        "organic_mr": "झाड निरोगी आहे! नियमित वाढीसाठी जीवामृत आणि सूक्ष्मअन्नद्रव्यांची फवारणी चालू ठेवा.",
        "organic_hi": "पौधा पूरी तरह स्वस्थ है! नियमित पोषण के लिए जीवामृत या वर्मीवाश का उपयोग जारी रखें।",
        "organic_en": "Plant is healthy! Maintain regular watering and organic nutrients like vermiwash.",
        "chemical_mr": "कोणत्याही रासायनिक औषधाची गरज नाही. संतुलित NPK खते द्या.",
        "chemical_hi": "किसी रासायनिक कीटनाशक की आवश्यकता नहीं है। संतुलित उर्वरक दें।",
        "chemical_en": "No pesticide required. Maintain balanced balanced NPK fertilizer schedule.",
        "preventive_mr": "नियमितपणे किडींचे निरीक्षण करा आणि शेत स्वच्छ ठेवा.",
        "preventive_hi": "नियमित निगरानी बनाए रखें।",
        "preventive_en": "Continue routine scouting and maintain clean field borders."
    },
    {
        "crop": "Pomegranate",
        "class_name": "Pomegranate___Bacterial_Blight",
        "name_en": "Pomegranate Bacterial Blight (Telya)",
        "name_mr": "डाळिंबावरील तेल्या रोग (Bacterial Blight - Telya)",
        "name_hi": "अनार का जीवाणु झुलसा (तेलिया रोग)",
        "is_healthy": False,
        "organic_mr": "दशपर्णी अर्क किंवा जीवामृत फवारा. छाटणीनंतर जखमांवर बोर्डो पेस्ट (१०%) लावा. सोलापूर भागात तेल्यासाठी हवामान कोरडे ठेवावे.",
        "organic_hi": "दशपर्णी अर्क का छिड़काव करें। छंटाई के बाद तने पर बोर्डो लेप लगाएं।",
        "organic_en": "Apply Bordeaux paste (10%) on cut stems. Spray Dashaparni extract. Keep orchard clean.",
        "chemical_mr": "स्ट्रेप्टोसायक्लिन (Streptocycline) ०.५ ग्रॅम + कॉपर ऑक्सिक्लोराईड २.५ ग्रॅम प्रति लिटर पाण्यात मिसळून १५ दिवसांच्या अंतराने फवारा.",
        "chemical_hi": "स्ट्रेप्टोसाइक्लिन (0.5 ग्राम) + कॉपर ऑक्सीक्लोराइड (2.5 ग्राम) प्रति लीटर पानी में मिलाकर छिड़कें।",
        "chemical_en": "Spray Streptocycline @ 0.5g + Copper Oxychloride @ 2.5g per litre of water at 15-day intervals.",
        "preventive_mr": "बाधित फांद्या, पाने व फळे गोळा करून जाळून नष्ट करा. छाटणीची अवजारे सोडिअम हायपोक्लोराईटने निर्जंतुक करा.",
        "preventive_hi": "संक्रमित टहनियों और फलों को इकट्ठा करके जला दें। औजारों को सैनिटाइज करें।",
        "preventive_en": "Prune and burn infected shoots. Disinfect pruning shears with 1% sodium hypochlorite."
    },
    {
        "crop": "Pomegranate",
        "class_name": "Pomegranate___Cercospora_Leaf_Spot",
        "name_en": "Pomegranate Cercospora Spot",
        "name_mr": "डाळिंबावरील पानांवरील ठिपके (Cercospora Spot)",
        "name_hi": "अनार की पत्ती का धब्बा रोग",
        "is_healthy": False,
        "organic_mr": "५% गोमूत्र अर्क किंवा व्हर्मिवॉश फवारा. ट्रायकोडर्मा हरजिअनम ५ ग्रॅम/लिटर वापरा.",
        "organic_hi": "गोमूत्र अर्क (5%) या ट्राइकोडर्मा हरजिएनम (5 ग्राम/लीटर) का छिड़काव करें।",
        "organic_en": "Spray cow urine distillate (5%) or Trichoderma harzianum @ 5g/L.",
        "chemical_mr": "डायफेनोकोनॅझोल (Score) १ मिली किंवा कार्बेन्डाझिम + मँकोझेब (Saaf) २ ग्रॅम/लिटर पाण्यात फवारा.",
        "chemical_hi": "डाइफेनोकोनाजोल (1 मिली/लीटर) या कार्बेंडाजिम + मैंकोजेब (2 ग्राम/लीटर) का छिड़काव करें।",
        "chemical_en": "Spray Difenoconazole 25% EC (Score) @ 1ml/L or Carbendazim + Mancozeb (Saaf) @ 2g/L water.",
        "preventive_mr": "झाडावर पाण्याचा ताण येऊ देऊ नका. फळबागेत सूर्यप्रकाश पोहोचेल अशी छाटणी ठेवा.",
        "preventive_hi": "बगीचे में धूप और हवा का आवागमन सुनिश्चित करें।",
        "preventive_en": "Ensure proper canopy management for adequate sunlight penetration."
    },
    {
        "crop": "Pomegranate",
        "class_name": "Pomegranate___Anthracnose",
        "name_en": "Pomegranate Anthracnose",
        "name_mr": "डाळिंबावरील अँथ्रॅकनोज / काळे डाग",
        "name_hi": "अनार का एन्थ्रेक्नोज (काला धब्बा)",
        "is_healthy": False,
        "organic_mr": "बोर्डो मिश्रण १% किंवा निंबोळी तेल १० मिली/लिटर फवारा.",
        "organic_hi": "1% बोर्डो मिश्रण या नीम का तेल (10 मिली/लीटर) का छिड़काव करें।",
        "organic_en": "Spray 1% Bordeaux mixture or Neem oil @ 10ml/L.",
        "chemical_mr": "अझॉक्सीस्ट्रॉबिन (Amistar) १ मिली किंवा प्रोपिकोनाझोल (Tilt) १ मिली प्रति लिटर पाण्यात फवारा.",
        "chemical_hi": "एजॉक्सीस्ट्रोबिन (1 मिली/लीटर) या प्रोपिकोनाजोल (1 मिली/लीटर) पानी में मिलाकर छिड़कें।",
        "chemical_en": "Spray Azoxystrobin 23% SC @ 1ml/L or Propiconazole 25% EC @ 1ml/L water.",
        "preventive_mr": "पावसाळ्याच्या सुरुवातीला बुरशीनाशकाची प्रतिबंधात्मक फवारणी करावी.",
        "preventive_hi": "मानसून की शुरुआत में निवारक स्प्रे करें।",
        "preventive_en": "Apply protective fungicide before monsoon showers commence."
    },
    {
        "crop": "Pomegranate",
        "class_name": "Pomegranate___Healthy",
        "name_en": "Healthy Pomegranate",
        "name_mr": "निरोगी डाळिंब झाड",
        "name_hi": "स्वस्थ अनार का पौधा",
        "is_healthy": True,
        "organic_mr": "झाड उत्तम स्थितीत आहे! ताकद टिकवण्यासाठी शेणखत आणि फॉस्फरस सोल्यूबिलायझिंग बॅक्टेरिया द्या.",
        "organic_hi": "अनार का पौधा स्वस्थ है! जैविक खाद और सूक्ष्म पोषक तत्व देते रहें।",
        "organic_en": "Pomegranate foliage is healthy! Continue standard nutrient fertigation.",
        "chemical_mr": "कोणत्याही औषधाची फवारणी आवश्यक नाही.",
        "chemical_hi": "किसी कीटनाशक की आवश्यकता नहीं है।",
        "chemical_en": "No chemical treatment needed.",
        "preventive_mr": "नियमित पाणी नियोजन आणि तण नियंत्रण ठेवा.",
        "preventive_hi": "उचित सिंचाई और खरपतवार नियंत्रण बनाए रखें।",
        "preventive_en": "Maintain consistent drip irrigation and orchard sanitation."
    },
    {
        "crop": "Onion",
        "class_name": "Onion___Purple_Blotch",
        "name_en": "Onion Purple Blotch",
        "name_mr": "कांद्यावरील जांभळा करपा (Purple Blotch)",
        "name_hi": "प्याज का बैंगनी धब्बा रोग",
        "is_healthy": False,
        "organic_mr": "५% गोमूत्र अर्क आणि हिंग पावडरचे द्रावण फवारा. सेंद्रिय डिंक (स्टिकर) अवश्य वापरा.",
        "organic_hi": "नीम का काढ़ा और गौमूत्र का छिड़काव करें। घोल में चिपचिपा पदार्थ (स्टिकर) अवश्य मिलाएं।",
        "organic_en": "Spray 5% fermented cow urine or neem seed extract with organic wetting agent.",
        "chemical_mr": "टेबुकोनाझोल + ट्रायफ्लॉक्सिस्ट्रॉबिन (Nativo) ०.७ ग्रॅम/लिटर किंवा मँकोझेब २.५ ग्रॅम + स्टिकर १ मिली/लिटर मिसळून फवारा.",
        "chemical_hi": "टेबुकोनाजोल + ट्राइफ्लॉक्सीस्ट्रोबिन (नेटिवो - 0.7 ग्राम/लीटर) या मैंकोजेब (2.5 ग्राम/लीटर) स्टिकर के साथ छिड़कें।",
        "chemical_en": "Spray Tebuconazole + Trifloxystrobin (Nativo) @ 0.7g/L or Mancozeb @ 2.5g/L with non-ionic sticker.",
        "preventive_mr": "कांद्याच्या पानांवर मेणाचा थर असल्याने फवारणीत 'स्टिकर' (Wetting Agent) टाकणे अत्यंत गरजेचे आहे.",
        "preventive_hi": "प्याज की पत्तियों पर मोम की परत होती है, अतः किसी भी स्प्रे में स्टिकर (चिपकने वाला घोल) अवश्य मिलाएं।",
        "preventive_en": "Always add a spreader/sticker (surfactant) because onion leaves have a waxy cuticle."
    },
    {
        "crop": "Onion",
        "class_name": "Onion___Downy_Mildew",
        "name_en": "Onion Downy Mildew",
        "name_mr": "कांद्यावरील केवडा / डाऊनी मिल्ड्यू (Downy Mildew)",
        "name_hi": "प्याज का डाउनी फफूंद (केवड़ा रोग)",
        "is_healthy": False,
        "organic_mr": "बोर्डो मिश्रण ०.८% किंवा तांबेयुक्त सेंद्रिय बुरशीनाशक फवारा. शेतात साचलेले पाणी त्वरित काढून टाका.",
        "organic_hi": "0.8% बोर्डो मिश्रण का छिड़काव करें। खेत में अतिरिक्त पानी न रुकने दें।",
        "organic_en": "Spray 0.8% Bordeaux mixture. Ensure field is not waterlogged.",
        "chemical_mr": "डायमेथोमॉर्फ (Acrobat) १ ग्रॅम + मँकोझेब २ ग्रॅम प्रति लिटर पाण्यात मिसळून फवारा.",
        "chemical_hi": "डाइमेथोमोर्फ (1 ग्राम/लीटर) + मैंकोजेब (2 ग्राम/लीटर) पानी में मिलाकर छिड़कें।",
        "chemical_en": "Spray Dimethomorph 50% WP @ 1g/L + Mancozeb 75% WP @ 2g/L with wetting agent.",
        "preventive_mr": "सकाळच्या दव आणि दाट धुक्यात रोगाचा प्रादुर्भाव वाढतो. गादीवाफ्यावर लागवड करा.",
        "preventive_hi": "सवेरे ओस और अत्यधिक नमी में रोग फैलता है। जल निकास उत्तम रखें।",
        "preventive_en": "Disease thrives in cool foggy mornings. Plant on raised beds with proper spacing."
    },
    {
        "crop": "Onion",
        "class_name": "Onion___Healthy",
        "name_en": "Healthy Onion",
        "name_mr": "निरोगी कांदा पीक",
        "name_hi": "स्वस्थ प्याज की फसल",
        "is_healthy": True,
        "organic_mr": "कांद्याची पात निरोगी आहे! गंधक (Sulphur) खताचा योग्य वापर कांद्याचा आकार व रंग चांगला करतो.",
        "organic_hi": "फसल पूरी तरह स्वस्थ है! कंद के विकास के लिए सल्फर का उचित उपयोग करें।",
        "organic_en": "Onion crop is vigorous and healthy! Apply recommended sulphur for bulb quality.",
        "chemical_mr": "कोणत्याही रासायनिक औषधाची गरज नाही.",
        "chemical_hi": "रासायनिक दवा की आवश्यकता नहीं है।",
        "chemical_en": "No chemical treatment needed.",
        "preventive_mr": "कांदा पोसण्याच्या काळात नियमित पाणी द्या, परंतु पाणी साचू देऊ नका.",
        "preventive_hi": "कंद बनने के दौरान नियमित और नियंत्रित सिंचाई करें।",
        "preventive_en": "Maintain consistent irrigation during bulb enlargement."
    }
]

def seed_database_diseases(db: Session):
    """Populates diseases and treatments tables on first run."""
    for item in INITIAL_CROP_KNOWLEDGE:
        existing = db.query(Disease).filter(Disease.model_class_name == item["class_name"]).first()
        if not existing:
            disease = Disease(
                crop_name=item["crop"],
                model_class_name=item["class_name"],
                common_name_en=item["name_en"],
                common_name_mr=item["name_mr"],
                common_name_hi=item["name_hi"],
                is_healthy=item["is_healthy"]
            )
            db.add(disease)
            db.commit()
            db.refresh(disease)

            treatment = Treatment(
                disease_id=disease.id,
                organic_mr=item["organic_mr"],
                organic_hi=item["organic_hi"],
                organic_en=item["organic_en"],
                chemical_mr=item["chemical_mr"],
                chemical_hi=item["chemical_hi"],
                chemical_en=item["chemical_en"],
                preventive_mr=item["preventive_mr"],
                preventive_hi=item["preventive_hi"],
                preventive_en=item["preventive_en"]
            )
            db.add(treatment)
            db.commit()
    print("[*] Database verified and seeded with 12 crop disease treatments.")


def get_disease_info_and_treatment(db: Session, model_class_name: str, lang: str = "mr"):
    """
    Fetches the localized name, symptoms, and treatment for a predicted disease.
    Defaults to Marathi ('mr').
    """
    disease = db.query(Disease).filter(Disease.model_class_name == model_class_name).first()
    if not disease:
        return None

    # Pick localized common name
    if lang == "mr":
        disease_name = disease.common_name_mr
    elif lang == "hi":
        disease_name = disease.common_name_hi
    else:
        disease_name = disease.common_name_en

    t = disease.treatment
    if not t:
        return None

    # Pick localized treatment advice
    if lang == "mr":
        organic = t.organic_mr
        chemical = t.chemical_mr
        preventive = t.preventive_mr
        officer_note = t.officer_note_mr
    elif lang == "hi":
        organic = t.organic_hi
        chemical = t.chemical_hi
        preventive = t.preventive_hi
        officer_note = t.officer_note_hi
    else:
        organic = t.organic_en
        chemical = t.chemical_en
        preventive = t.preventive_en
        officer_note = t.officer_note_en

    return {
        "disease_id": disease.id,
        "crop_name": disease.crop_name,
        "disease_name": disease_name,
        "is_healthy": disease.is_healthy,
        "organic": organic,
        "chemical": chemical,
        "preventive": preventive,
        "officer_note": officer_note
    }
