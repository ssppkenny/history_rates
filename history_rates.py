import urllib.request
from pprint import pprint
from html_table_parser import HTMLTableParser
import re
import pandas as pd
import matplotlib.pyplot as plt
from collections import namedtuple
from concurrent.futures import ProcessPoolExecutor

plt.style.use('fivethirtyeight')
plt.rcParams['figure.figsize'] = [20, 20]


Selection = namedtuple('Selection', ['day', 'month', 'year_from', 'year_to'])


class FxtopRate:
    
    def __init__(self, date_str, from_cur, to_cur, years=1):
        self._date_str = date_str
        self._from_cur = from_cur
        self._to_cur = to_cur
        self._years = years
        date_parts = re.findall('(\d{4})(\d{2})(\d{2})', date_str)
        year = int(date_parts[0][0])
        day = date_parts[0][2]
        month = date_parts[0][1]
        year_from = str(year-1)
        year_to = year
        self._selection = Selection(day, month, year_from, year_to)
       
    def _data_from_selection(self, selection):
        """
        builds from date_str and returns the url for request
        """
        day = selection.day
        month = selection.month
        year_from = selection.year_from
        year_to = selection.year_to
        
        from_cur = self._from_cur
        to_cur = self._to_cur
        url = f"https://fxtop.com/en/historical-exchange-rates.php?A=1&C1={from_cur}&C2={to_cur}&TR=1&DD1={day}&MM1={month}&YYYY1={year_from}&B=1&P=&I=1&DD2={day}&MM2={month}&YYYY2={year_to}&btnOK=Go%21"
        
        html = self._get_html(selection, url)
        p = HTMLTableParser()
        p.feed(html)
        df = pd.DataFrame.from_records(p.tables[26][6:])
        df[0] = pd.to_datetime(df[0])
        df[1] = pd.to_numeric(df[1])
        
        return df
    
    
    def _get_html(self, selection, url):
        fp = urllib.request.urlopen(url)
        return fp.read().decode("utf-8")
    
    def get_rates(self):
        selection = self._selection
        pool = ProcessPoolExecutor(4)
        reqs = []
        for i in range(self._years,0, -1):
            req = pool.submit(self._data_from_selection, selection)
            reqs.append(req)
            selection = self._next_selection(selection)
            
        df = pd.DataFrame()
        for req in reqs:
            df = pd.concat([df, req.result()])
             
        return df
    
    def _next_selection(self, selection):
        return Selection(selection.day, selection.month, str(int(selection.year_from)-1), str(int(selection.year_to)-1))
    
    def plot(self):
        df = self.get_rates()
        fig = plt.figure()
        plt.title(f"Exchange rates on {self._date_str} from {self._from_cur} to {self._to_cur}" )
        plt.xlabel("Date")
        plt.ylabel("Exchange Rate")
        plt.plot(df[0], df[1])

        
    

