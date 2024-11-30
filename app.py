from flask import Flask, request, render_template
import pandas as pd
import plotly.express as px
import os

app = Flask(__name__)

# CSV 및 Excel 데이터 읽기
data1 = pd.read_csv('data1.csv', encoding='cp949')
data2 = pd.read_excel('data2.xlsx')
data3 = pd.read_excel('data3.xlsx')
data4 = pd.read_excel('data4.xlsx')

data = pd.concat([data1, data2, data3, data4], axis=1)
columns_list = data.columns.tolist()

# summary 데이터 읽기
summary_1 = pd.read_excel('summary_광고비처리1.xlsx')
summary_2 = pd.read_excel('summary_광고비처리2.xlsx')

# 가중치 설정
weights = {
    '맛있음': 10,
    '위생': 8,
    '서비스': 6,
    '분위기': 5,
    '위치접근성': 4,
    '대기시간': 3,
    '가성비': 2,
    '가격': 1
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    # 사용자 입력 받기
    rank = request.form['rank'].split(", ")

    # 가중치 계산
    ranked_weights = {criterion: weights[criterion] * (len(rank) - i) for i, criterion in enumerate(rank)}

    # 추천 점수 계산 함수
    def calculate_scores(summary_df):
        summary_df['추천 점수'] = summary_df.apply(
            lambda row: row['긍정도 (%)'] * ranked_weights.get(row['클래스 설명'], 0)
            if row['클래스 설명'] in ranked_weights else 0,
            axis=1
        )
        # 식당별 점수 합산 및 정렬
        final_scores = summary_df.groupby('식당 이름')['추천 점수'].sum().sort_values(ascending=False)
        # 식당 이름 추출
        final_scores_renamed = final_scores.rename(
            lambda x: columns_list[int(x.split('_')[1]) - 1]
        )
        return final_scores_renamed

    # 각각의 summary 결과 계산
    scores_1 = calculate_scores(summary_1)
    scores_2 = calculate_scores(summary_2)

    # 결과 통합
    result_1 = scores_1.to_frame(name='추천 점수 1').reset_index()
    result_2 = scores_2.to_frame(name='추천 점수 2').reset_index()

    merged_results = pd.merge(result_1, result_2, on='식당 이름', how='outer').fillna(0)

    # Plotly로 그래프 생성
    fig = px.bar(
        merged_results.melt(id_vars='식당 이름', var_name='데이터셋', value_name='추천 점수'),
        x='추천 점수',
        y='식당 이름',
        color='데이터셋',
        barmode='group',
        title="추천 식당 순위 비교",
        text='추천 점수'
    )
    fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')
    fig.update_layout(yaxis={'categoryorder': 'total ascending'})

    # 그래프를 HTML로 변환
    graph_html = fig.to_html(full_html=False)
    return render_template('result.html', graph_html=graph_html)

if __name__ == '__main__':
    #app.run(debug=True)
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
