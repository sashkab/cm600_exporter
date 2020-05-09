from .. import *

import pytest
import requests


@pytest.fixture
def tcollector(monkeypatch, tmp_path):
    config_file = tmp_path.joinpath("cm600.ini")
    config_file.write_text("[cable_modem]\nuser=admin\npass=password\n")

    monkeypatch.setenv("CM600_CONFIG", str(config_file))

    html_file = Path(__file__).parent.joinpath('page.html')
    c = Collector()

    c.page = html_file.read_text()
    c.seconds_between_fetch = 3600
    return c


def test_collector_0(tcollector, monkeypatch):
    assert tcollector.authinfo == ("admin", "password")


def test_collector_1(monkeypatch):
    monkeypatch.delenv("CM600_CONFIG", raising=False)
    c = Collector()
    assert c.authinfo == (None, None)


def test_collector_2(monkeypatch, tmp_path):
    monkeypatch.delenv("CM600_CONFIG", raising=False)
    config_file = tmp_path.joinpath("cm600.ini")
    config_file.write_text("[xxx]\n")
    monkeypatch.setenv("CM600_CONFIG", str(config_file))
    with pytest.raises(ValueError) as err:
        c = Collector()
    assert err.value.args[0] == f"Missing username/password for cable modem in '{config_file}'."


def test_collector_3(monkeypatch, tmp_path):
    monkeypatch.delenv("CM600_CONFIG", raising=False)
    config_file = tmp_path.joinpath("cm600.ini")
    config_file.write_text("[cable_modem]\n")
    monkeypatch.setenv("CM600_CONFIG", str(config_file))
    c = Collector()
    assert c.authinfo == (None, None)
    assert str(c.config_file) == str(config_file)

def test_collector_4(monkeypatch, tmp_path):
    monkeypatch.delenv("CM600_CONFIG", raising=False)
    c = Collector(username='admin', password='password')
    assert c.authinfo == ("admin", "password")


@pytest.mark.parametrize('h, r', [
    ("Shit happens", "shit_happens"),
    ("blah 100%", "blah_100_"),
])
def test__make_header(tcollector, h, r):
    assert tcollector._make_header(h) == r


@pytest.mark.parametrize('h, r', [
    ("100 dB", "100"),
    ("100.8 Mhz", "100.8"),
])
def test__make_data(tcollector, h, r):
    assert tcollector._make_data(h) == r


def test_get_doc(tcollector):
    assert tcollector.get_doc('test') == "No Documentation"


def test_get_table0(tcollector):
    t = tcollector.get_table('dsTable')
    assert 'id="dsTable"' in str(t)

    t = tcollector.get_table('usTable')
    assert 'id="usTable"' in str(t)


def test_get_table1(tcollector, requests_mock):
    requests_mock.get(tcollector.url, text=tcollector.page)
    tcollector.page=None

    t = tcollector.get_table('dsTable')
    assert 'id="dsTable"' in str(t)

    t = tcollector.get_table('usTable')
    assert 'id="usTable"' in str(t)


def test_parse_html_table(tcollector):
    assert tcollector.parse_html_table('dsTable')[0] == {'channel': '1',
        'channel_id': '5',
        'correctables': '65461',
        'frequency': '603000000 Hz',
        'lock_status': 'Locked',
        'modulation': 'QAM256',
        'power': '3.9 dBmV',
        'snr': '39.7 dB',
        'uncorrectables': '0'
    }

    assert tcollector.parse_html_table('usTable')[0] == {
        'channel': '1',
        'channel_id': '1',
        'frequency': '14000000 Hz',
        'lock_status': 'Locked',
        'power': '44.8 dBmV',
        'symbol_rate': '5120 Ksym/sec',
        'us_channel_type': 'ATDMA'
    }


def test_make_metric0(tcollector):
    m = tcollector.make_metric('abc', 1.23, 'test', dict(), False)
    assert str(m) == "Metric(abc, test, gauge, , [Sample(name='abc', labels={}, value=1.23, timestamp=None, exemplar=None)])"

def test_make_metric1(tcollector):
    m = tcollector.make_metric('abc', 1.23, 'test', dict(), True)
    assert str(m) == "Metric(abc, test, counter, , [Sample(name='abc_total', labels={}, value=1.23, timestamp=None, exemplar=None)])"


def test_process_table(tcollector):
    tbl = [{
        'frequency': '120 hz',
        'symbol_rate': '1 symbol',
        'channel_id': '42',
        'power': '3.2 dBmV',
    }]

    c = tcollector.process_table('prefix', tbl)

    assert len(c) == 2
    assert str(c[0]) == "Metric(prefix_power, No Documentation, gauge, , [Sample(name='prefix_power', labels={'channel_id': '42', 'frequency': '120 hz'}, value=3.2, timestamp=None, exemplar=None)])"
    assert str(c[1]) == "Metric(prefix_state, No Documentation, gauge, , [Sample(name='prefix_state', labels={'channel_id': '42', 'frequency': '120 hz'}, value=1, timestamp=None, exemplar=None)])"


def test_collect(tcollector):
    c = tcollector.collect()
    # FIXME

    assert len(c) == 168
