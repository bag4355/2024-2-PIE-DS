from flask import Flask, request, render_template
import pandas as pd
import plotly.express as px

app = Flask(__name__)

# 데이터 로드
data1 = pd.read_csv('data1.csv', encoding='cp949')
data2 = pd.read_excel('data2.xlsx')
data3 = pd.read_excel('data3.xlsx')
data4 = pd.read_excel('data4.xlsx')

data = pd.concat([data1, data2, data3, data4], axis=1)
columns_list = data.columns.tolist()

summary_1 = pd.read_excel('summary_광고비처리.xlsx')
summary_2 = pd.read_excel('summary_찐리뷰만.xlsx')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    # 사용자 입력 받기
    user_weights = {
        '맛있음': int(request.form['맛있음']),
        '위생': int(request.form['위생']),
        '서비스': int(request.form['서비스']),
        '분위기': int(request.form['분위기']),
        '위치접근성': int(request.form['위치접근성']),
        '대기시간': int(request.form['대기시간']),
        '가성비': int(request.form['가성비']),
        '가격': int(request.form['가격']),
    }

    score_threshold = float(request.form.get('score_threshold', 0))
    sort_by = request.form.get('sort_by', '평균 점수')

    # 점수 계산 함수
    def calculate_scores(summary_df):
        summary_df['추천 점수'] = summary_df.apply(
            lambda row: row['긍정도 (%)'] * user_weights.get(row['클래스 설명'], 0)
            if row['클래스 설명'] in user_weights else 0,
            axis=1
        )
        final_scores = summary_df.groupby('식당 이름')['추천 점수'].sum().sort_values(ascending=False)
        final_scores_renamed = final_scores.rename(
            lambda x: columns_list[int(x.split('_')[1]) - 1]
        )
        return final_scores_renamed

    # 각각의 summary 결과 계산
    scores_1 = calculate_scores(summary_1)
    scores_2 = calculate_scores(summary_2)

    # 결과 통합
    result_1 = scores_1.to_frame(name='광고성 리뷰 포함').reset_index()
    result_2 = scores_2.to_frame(name='광고성 리뷰 제거').reset_index()

    merged_results = pd.merge(result_1, result_2, on='식당 이름', how='outer').fillna(0)

    # 평균 점수 계산 및 필터링
    merged_results['평균 점수'] = merged_results[['광고성 리뷰 포함', '광고성 리뷰 제거']].mean(axis=1)
    merged_results = merged_results[merged_results['평균 점수'] >= score_threshold]

    # 정렬
    merged_results = merged_results.sort_values(by=sort_by, ascending=False).head(5)

    # Plotly로 그래프 생성
    fig = px.bar(
        merged_results.melt(id_vars='식당 이름', var_name='데이터셋', value_name='추천 점수'),
        x='추천 점수',
        y='식당 이름',
        color='데이터셋',
        barmode='group',
        title="신촌 식당 추천 결과",
        text='추천 점수'
    )
    fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')
    fig.update_layout(
        yaxis={'categoryorder': 'total ascending'},
        annotations=[
            dict(
                text="제작자: 산업공학회 PIE 24-2 DS 학회원 강태희, 고민지, 김건우, 김세원, 김채연, 안성진",
                xref="paper", yref="paper",
                x=0, y=-0.2,
                showarrow=False
            )
        ]
    )

    # HTML 그래프 생성
    graph_html = fig.to_html(full_html=False)
    return render_template('result.html', graph_html=graph_html)

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))  # Render에서 제공하는 포트를 가져옴
    app.run(host='0.0.0.0', port=port)  # 0.0.0.0으로 외부에서 접속 가능하게 설정
