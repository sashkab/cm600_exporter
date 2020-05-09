"""Netgear CM600 Collector for Prometheus"""

__version__ = "0.0.2"

from datetime import datetime
from pathlib import Path
import configparser
import re
import os

import requests
from bs4 import BeautifulSoup
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily

# FIXME: use logger


class Collector:
    """Netgear CM600 collector for Prometheus"""

    _prefix = 'cm600'
    seconds_between_fetch = 30
    ids = ("channel_id", "frequency")
    counter = ("correctables", "uncorrectables")

    def __init__(self, url="http://192.168.100.1/DocsisStatus.asp", username=None, password=None):
        """Initialize"""

        self.page = None
        self.url = url
        self.last_fetch = datetime.now()
        self.config_file = Path(os.environ.get('CM600_CONFIG') or "cabemodem.ini").expanduser()

        if username is None:
            self.authinfo = self.get_authinfo()
        else:
            self.authinfo = (username, password)

    def get_authinfo(self):
        """Retreive authentication information from config file"""

        if not self.config_file.exists():
            return None, None
        print(f"Reading {self.config_file}...")
        config = configparser.ConfigParser()
        config.read(self.config_file)
        if 'cable_modem' in config.sections():
            ini = config['cable_modem']
            return ini.get('user', None), ini.get('pass', None)

        raise ValueError(f"Missing username/password for cable modem in '{self.config_file}'.")

    def get_table(self, table_id):
        """return requested table"""

        now = datetime.now()
        print(f"get_table, {(now - self.last_fetch).seconds}", flush=True)
        if self.page is None or (now - self.last_fetch).seconds > self.seconds_between_fetch:
            print(f"Fetching {self.url}", flush=True)
            r = requests.get(self.url, auth=self.authinfo)
            r.raise_for_status()
            self.page = r.text
            self.last_fetch = now

        soup = BeautifulSoup(self.page, 'html.parser')
        return soup.find("table", {"id": table_id})

    def _make_header(self, text):
        """lower case and replace special symbols with underscores"""

        return re.sub(r"[^a-z0-9]", "_", text.lower().strip())

    def _make_data(self, text):
        """strip letters"""

        return text.split()[0]

    def _process_row(self, row, is_header=False):
        """process row of the table"""

        if is_header:
            func = self._make_header
        else:
            func = lambda x: x
        return  [func(ele.text.strip()) for ele in row.find_all('td') if ele.text.strip()]

    def parse_html_table(self, table_name):
        """Parse html table, return list of dicts"""

        rows = self.get_table(table_name).find_all('tr')
        header = [self._make_header(h) for h in self._process_row(rows[0], is_header=True)]
        return [dict(zip(header, self._process_row(row))) for row in rows[1:]]

    def get_doc(self, name):
        """return documentation string for field"""

        docs = {
            # FIXME
        }
        return docs.get(name, "No Documentation")

    def make_metric(self, name, value, doc, labels, is_counter=False):
        """Return prometheus metric"""
        func = CounterMetricFamily if is_counter else GaugeMetricFamily
        m = func(name, doc, labels=list(labels.keys()))
        m.add_metric(list(labels.values()), value)
        return m

    def process_table(self, prefix, table):
        """Converts table into list of Prometheus metrics."""

        data = []
        for row in table:
            state = {}
            labels = {k: row[k] for k in self.ids}
            for k, v in row.items():
                if k in self.ids:
                    continue
                if re.match(r"^-?[0-9\.]+( .*)?", v) and k not in ("frequency", "symbol_rate"):
                    data.append(self.make_metric(f"{prefix}_{k}", float(v.split(" ")[0]), self.get_doc(k), labels, k in self.counter))
                else:
                    state[k] = v
            if state:
                state.update(labels)
                data.append(self.make_metric(f"{prefix}_state", 1, self.get_doc("state"), labels, False))
        return data

    def collect(self):
        """Returns metrics to prometheus client"""

        metrics = []
        metrics.extend(self.process_table(f"{self._prefix}_downstream", self.parse_html_table('dsTable')))
        metrics.extend(self.process_table(f"{self._prefix}_upstream", self.parse_html_table('usTable')))

        return metrics
