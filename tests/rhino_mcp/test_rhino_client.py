"""Tests for the Rhino client module."""
from typing import Dict, Any, Optional, List, Tuple, Union, TypedDict, Generator
import socket
import threading
import time
import json
import pytest
from pytest.monkeypatch import MonkeyPatch
from pytest.logging import LogCaptureFixture

from rhino_mcp.rhino_client import RhinoClient, Point3d


class MockSocket:
    """Mock socket for testing."""
    
    def __init__(self) -> None:
        """Initialize mock socket."""
        self.sent_data: List[bytes] = []
        self.responses: List[bytes] = []
    
    def connect(self, addr: Tuple[str, int]) -> None:
        """Mock connect method."""
        pass
    
    def sendall(self, data: bytes) -> None:
        """Mock sendall method to record sent data."""
        self.sent_data.append(data)
    
    def recv(self, bufsize: int) -> bytes:
        """Mock recv method to return pre-configured responses."""
        if not self.responses:
            return b""
        return self.responses.pop(0)
    
    def close(self) -> None:
        """Mock close method."""
        pass
    
    def add_response(self, response: Dict[str, Any]) -> None:
        """Add a response to the mock socket."""
        self.responses.append(json.dumps(response).encode('utf-8'))


@pytest.fixture
def mock_socket(monkeypatch: MonkeyPatch) -> Generator[MockSocket, None, None]:
    """Create a mock socket for testing."""
    mock = MockSocket()
    
    # Mock socket.socket to return our mock
    def mock_socket_constructor(*args: Any, **kwargs: Any) -> MockSocket:
        return mock
    
    monkeypatch.setattr(socket, "socket", mock_socket_constructor)
    
    yield mock


def test_rhino_client_connect(mock_socket: MockSocket) -> None:
    """Test RhinoClient connect method."""
    client = RhinoClient()
    
    # Test successful connection
    assert client.connect() is True
    assert client.connected is True


def test_rhino_client_ping(mock_socket: MockSocket) -> None:
    """Test RhinoClient ping method."""
    client = RhinoClient()
    client.connect()
    
    # Add mock response for ping
    mock_socket.add_response({
        'status': 'success',
        'message': 'Rhino is connected',
        'data': {
            'version': '8.0.0',
            'has_active_doc': True,
            'server_version': 'RhinoMCP-1.0',
            'server_start_time': '2025-03-13 21:00:00',
            'script_path': 'C:\\path\\to\\rhino_server.py'
        }
    })
    
    # Test ping
    response = client.ping()
    
    # Verify request was sent
    assert len(mock_socket.sent_data) == 1
    request = json.loads(mock_socket.sent_data[0].decode('utf-8'))
    assert request['type'] == 'ping'
    
    # Verify response was parsed correctly
    assert response['status'] == 'success'
    assert response['message'] == 'Rhino is connected'
    assert 'data' in response
    assert response['data']['version'] == '8.0.0'


def test_rhino_client_create_curve(mock_socket: MockSocket) -> None:
    """Test RhinoClient create_curve method."""
    client = RhinoClient()
    client.connect()
    
    # Add mock response for create_curve
    mock_socket.add_response({
        'status': 'success',
        'message': 'Curve created with 3 points',
        'data': {
            'id': '12345-67890',
            'point_count': 3
        }
    })
    
    # Test points
    points: List[Point3d] = [
        {'x': 0.0, 'y': 0.0, 'z': 0.0},
        {'x': 5.0, 'y': 10.0, 'z': 0.0},
        {'x': 10.0, 'y': 0.0, 'z': 0.0}
    ]
    
    # Test create_curve
    response = client.create_curve(points)
    
    # Verify request was sent
    assert len(mock_socket.sent_data) == 1
    request = json.loads(mock_socket.sent_data[0].decode('utf-8'))
    assert request['type'] == 'create_curve'
    assert 'data' in request
    assert 'points' in request['data']
    assert len(request['data']['points']) == 3
    
    # Verify response was parsed correctly
    assert response['status'] == 'success'
    assert response['message'] == 'Curve created with 3 points'
    assert 'data' in response
    assert response['data']['id'] == '12345-67890'


def test_rhino_client_invalid_points() -> None:
    """Test RhinoClient create_curve with invalid points."""
    client = RhinoClient()
    
    # Test with empty points list
    with pytest.raises(ValueError):
        client.create_curve([])
    
    # Test with single point
    with pytest.raises(ValueError):
        client.create_curve([{'x': 0.0, 'y': 0.0, 'z': 0.0}])
