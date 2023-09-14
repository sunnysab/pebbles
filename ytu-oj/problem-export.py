
from typing import List
import requests
from bs4 import BeautifulSoup


class Problem:
    problem: int
    title: str
    difficulty: int

    def __init__(self, problem: int, title: str, difficulty: int):
        self.problem = problem
        self.title = title
        self.difficulty = difficulty
    

def get_problem_list() -> List[Problem]:

    session = requests.Session()

    def get_by_page(page_num: int) -> List[Problem]:
        url = f'https://oj.ytu.edu.cn/problemset.php?page={page_num}'
        html = session.get(url).text
        soup = BeautifulSoup(html, 'html.parser')

        result = []
        for each_problem in soup.find_all('tr')[1:]:
            colums = each_problem.find_all('td')
            problem_num = int(colums[1].text)
            title = colums[2].text.strip()
            passed = int(colums[4].text)
            submitted = int(colums[5].text)
            difficulty = passed * 1.0 / submitted if submitted != 0 else 0

            if submitted > 50:
                result.append(Problem(problem_num, title, difficulty))
        return result
    
    result = []
    for page in range(1, 32):
        result.extend(get_by_page(page))

    return sorted(result, key=lambda x: x.difficulty, reverse=True)


if __name__ == '__main__':
    result = get_problem_list()
    
    with open('problem-set.txt', 'w+') as fp:
        for each_problem in result:
            fp.write(f'{each_problem.problem}\t{each_problem.title}\t{each_problem.difficulty}\n')
        