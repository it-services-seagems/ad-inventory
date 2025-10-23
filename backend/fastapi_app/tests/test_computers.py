import pytest
from fastapi.testclient import TestClient

from ..main import app
from .. import managers


client = TestClient(app)


def test_list_computers_sql_monkeypatch(monkeypatch):
    # Arrange: replace sql_manager.get_computers_from_sql to return a known list
    def fake_get_computers():
        return [{'name': 'SHQABC123', 'dn': 'CN=SHQABC123,OU=Computers', 'dnsHostName': 'shqabc123.snm.local', 'disabled': False}]

    monkeypatch.setattr(managers.sql_manager, 'get_computers_from_sql', fake_get_computers)

    # Act
    resp = client.get('/api/computers?source=sql')

    # Assert
    assert resp.status_code == 200
    body = resp.json()
    assert body['source'] == 'sql'
    assert isinstance(body['items'], list)
    assert body['items'][0]['name'] == 'SHQABC123'


def test_toggle_status_ldap_fails_powershell_succeeds(monkeypatch):
    # Arrange: simulate LDAP toggle raising and PowerShell returning success
    def fake_toggle(computer_name, action):
        raise Exception('LDAP error')

    def fake_toggle_ps(computer_name, action):
        return {'success': True, 'message': 'PowerShell success', 'method': 'powershell'}

    monkeypatch.setattr(managers.ad_computer_manager, 'toggle_computer_status', fake_toggle)
    monkeypatch.setattr(managers.ad_computer_manager, 'toggle_computer_status_powershell', fake_toggle_ps)

    resp = client.post('/api/computers/SHQABC123/toggle-status', json={'action': 'enable', 'use_powershell': True})

    assert resp.status_code == 200
    body = resp.json()
    assert body.get('success') is True
    assert 'PowerShell' in body.get('message') or body.get('method') == 'powershell'
