# GPT5.4 Pro 기반 최신 레시피 데이터셋 검색, 간단 데이터 구조 확인

공식 페이지와 데이터 카드 기준으로 최신 업데이트 일자, 데이터 규모, 기본 필드 구조를 확인해 표로 정리하겠습니다. 공개 페이지에 없는 항목은 논문이나 저장소 설명으로 보완해 표시하겠습니다.

RecipeNLG와 Recipe1M+는 규모와 필드 확인이 거의 끝났고, Food.com은 Kaggle 노출 정보와 보조 메타데이터를 교차 검증해 날짜를 확정하는 중입니다.

핵심 쟁점은 업데이트 일자 해석이라, 원본 데이터 공개 시점과 미러·호스팅 페이지 수정일을 분리해 적겠습니다. 또 Hugging Face는 플랫폼 단위 대신 mbien/recipe_nlg 같은 개별 카드 기준으로 비교하고 있습니다.

Thought for 23m 32s

기준은 **“공개 페이지에서 확인 가능한 가장 최근 수정/업로드 시점”**입니다. 원본 발표 시점과 미러(Hugging Face, BERD 등) 수정 시점이 다르면 함께 적었습니다.

1) RecipeNLG
원본은 2020년 논문/프로젝트이고, 제가 확인한 가장 최근의 공개 수정은 Hugging Face 배포 카드 기준 2024-01-18입니다. 규모는 train split 2,231,142개이며 dataset_size는 2,194,783,815 bytes(약 2.19 GB)입니다. 구조는 id, title, ingredients[], directions[], link, source(Gathered/Recipes1M), ner[]로 꽤 정형화되어 있습니다.

2) Recipe1M+
원본 최신 citable release는 2019년 TPAMI 논문이고, 현재 공개 접근 안내는 공식 PyTorch 저장소에서 2024-01-14에 “recipe1M access”를 업데이트한 흔적이 보입니다. 규모는 100만+ 레시피와 1,300만 장 음식 이미지이며, 현재 README는 layer2+.json, LMDB/pickle/text 파일들과 함께 이미지 샤드 16개(Recipe1M+_{a..f}, Recipe1M+_{0..9})를 받도록 안내하고 있어 이미지 부분만 해도 다중 TB급입니다. 구조는 기본적으로 title/ingredients/instructions/images 조합이며, 영양 subset 예시는 id, ingredients{text}, instructions{text}, nutr_per_ingredient, quantity, unit, title, url, partition 같은 필드를 갖습니다.

3) Food.com Recipes and Interactions
원본 데이터셋 인용 연도는 2019년이고, Kaggle 노출면에서는 현재 **“Updated 5 years ago”**까지만 확인되며 정확한 날짜는 접근 가능한 페이지에 드러나지 않았습니다. 규모는 180K+ 레시피, 700K+ 리뷰, 수집 기간은 2000-02-25 ~ 2018-12-18, 크기는 0.89 GB입니다. 구조는 원시 파일 RAW_recipes.csv, RAW_interactions.csv와 함께, 가공본 기준 id, i, name_tokens, ingredient_tokens, steps_tokens, techniques, calorie_level, ingredient_ids, u, items, ratings, n_ratings 같은 필드를 포함합니다. 참고로 BERD 미러 레코드 메타데이터는 2025-07-31 수정으로 표시되지만, 이것은 미러 레코드의 수정일이지 원본 Kaggle 데이터 내용 수정일과는 다를 수 있습니다.

4) OpenRecipes
원본 GitHub 저장소는 2018-02-08에 archived 되었고, README는 이 데이터를 “recipe bookmarks” DB라고 설명하면서 조리 instructions는 포함하지 않는다고 명시합니다. 공개 덤프는 **20170107-061401-recipeitems.json.gz**이고, Hugging Face 미러는 2023-03-10 커밋으로 올라왔으며 미러 파일은 30.8 MB, size bucket은 **100K<n<1M**입니다. 구조는 _id, name, ingredients, url, image, ts, cookTime, source, recipeYield, datePublished, prepTime, description가 기본이고, 일부 레코드에는 totalTime, creator, recipeCategory, dateModified, recipeInstructions도 섞여 있어 스키마가 균일하지 않습니다.

5) 지난 Hugging Face 항목은 정정이 필요합니다
지난 답변에서 Hugging Face를 하나의 “레시피 데이터셋”처럼 묶은 것은 부정확했습니다. 실제로 Hugging Face에서 확인되는 RecipeNLG 카드는 mbien/recipe_nlg이고, 별도의 텍스트 레시피 데이터 예로는 Thefoodprocessor/recipes가 2023-11-13 커밋, 74,465 rows, 단일 recipe string 필드로 확인됩니다. 반면 제가 예시로 들었던 ethz/food101는 101,000 rows / 5.06 GB의 음식 이미지 데이터이며, 카드에도 ingredient list와 preparation method가 없다고 명시되어 있어서 “레시피 본문 데이터”로는 맞지 않습니다.

정리하면, frigo 같은 냉장고 기반 추천 서비스에 바로 쓰기 좋은 순서는 제 기준으로 RecipeNLG → Food.com → Recipe1M+ → OpenRecipes입니다. RecipeNLG는 스키마가 가장 단순하고 크기가 크며, Food.com은 사용자 상호작용이 붙어 있고, Recipe1M+는 이미지까지 강력하지만 접근 제약과 용량 부담이 크고, OpenRecipes는 instructions가 빠지거나 스키마가 들쭉날쭉해서 보조 데이터로 쓰는 편이 낫습니다.

다음 답변에서는 이 중에서 실제로 바로 다운로드 가능한 것만 추려서 링크, 라이선스, pandas로 읽는 코드까지 붙여드릴 수 있습니다.