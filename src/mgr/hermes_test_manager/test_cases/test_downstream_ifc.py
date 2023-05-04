"""Test cases for the downstream connection of an IPC-Hermes-9852 interface.

    >>>> Board transport direction >>>>
    ----------+          +----------
       System |          |  this
       under  | -------- |  code
       test   |          |
    ----------+          +----------
    thus an upstream connection is used by this test code 
    to send messages to the system under test.

    The test code does not know which lane interface is used,
    this is controlled by host/port configuration.
"""
import pytest

from test_cases import hermes_testcase
from test_cases import create_upstream_context, create_upstream_context_with_handshake
from test_cases import SYSTEM_UNDER_TEST_HOST, SYSTEM_UNDER_TEST_DOWNSTREAM_PORT
from ipc_hermes.connections import UpstreamConnection
from ipc_hermes.messages import Message, MAX_MESSAGE_SIZE

@hermes_testcase
def test_connect_disconnect_n_times():
    """Test connect and disconnect n times. No ServiceDescription sent."""
    for _ in range(10):
        with create_upstream_context():
            pass
    assert True

@hermes_testcase
def test_connect_service_description_disconnect_n_times():
    """Test connect and disconnect n times. 
       Send ServiceDescription but don't wait for answer before closing connection.
    """
    for _ in range(10):
        with create_upstream_context() as ctxt:
            ctxt.send_msg(Message.ServiceDescription("AcceptanceTest", 2))
    assert True

@hermes_testcase
@pytest.mark.testdriver
def test_connect_handshake_disconnect():
    """Test connect, send ServiceDescription, wait for answer, disconnect."""
    with create_upstream_context_with_handshake():
        pass
    assert True

# TODO: This test is not working as expected, original code returned success due to a bug
# when opening a second connection this way the first connection is closed
# @hermes_testcase
def test_connect_2_times():
    """Test to connect twice. Second connection should be rejected."""
    uc1 = UpstreamConnection()
    try:
        uc1.connect(SYSTEM_UNDER_TEST_HOST, SYSTEM_UNDER_TEST_DOWNSTREAM_PORT)
    except:
        uc1.close()
        raise

    uc2 = UpstreamConnection()
    try:
        uc2.connect(SYSTEM_UNDER_TEST_HOST, SYSTEM_UNDER_TEST_DOWNSTREAM_PORT)
    except ConnectionRefusedError:
        uc1.close()
        uc2.close()
        assert True
        return

    uc1.close()
    uc2.close()
    raise ValueError("second connection was accepted")

@hermes_testcase
def test_maximum_message_size():
    """Test maximum message size by sending a ServiceDescription message of max size.
       Success requires that the system under test responds with its own ServiceDescription.
    """
    with create_upstream_context() as ctxt:
        msg = Message.ServiceDescription("DownstreamId", 1)
        msg_bytes = msg.to_bytes()
        splitat = msg_bytes.find(b"LaneId=")
        dummy_attr = b'HermesAcceptanceTestDummyAttributeId="" '
        msg_bytes = msg_bytes[:splitat] + dummy_attr + msg_bytes[splitat:]
        splitat += len(dummy_attr) - 2
        extend_by = MAX_MESSAGE_SIZE - len(msg_bytes)
        msg_bytes = msg_bytes[:splitat] + extend_by * b"x" + msg_bytes[splitat:]
        ctxt.send_tag_and_bytes(msg.tag, msg_bytes)
        ctxt.expect_message("ServiceDescription")
    assert True

@hermes_testcase
def test_multiple_messages_per_packet():
    """Test sending multiple messages in one packet.
       A ServiceDescription message is inserted between two CheckAlive messages
       Success requires that the system under test responds with its own ServiceDescription.
       (None of the CheckAlive messages should be answered.)
    """
    with create_upstream_context() as ctxt:
        check_alive = Message.CheckAlive()
        service_description = Message.ServiceDescription("DownstreamId", 1)
        msg_bytes = check_alive.to_bytes() + service_description.to_bytes() + check_alive.to_bytes()
        ctxt.send_tag_and_bytes(service_description.tag, msg_bytes)
        ctxt.expect_message("ServiceDescription")
    assert True

@hermes_testcase
def xtest_terminate_on_illegal_message():
    """Test that connection is closed and reset when unknown message tags are recieved"""
    with create_upstream_context() as ctxt:
        illegal_msg_bytes = b"<Hermes Timestamp='2020-04-28T10:01:20.768'><ThisIsUnknownMessage /></Hermes>"
        ctxt.send_tag_and_bytes(None, illegal_msg_bytes)
        # other end has to close connection so check if socked is dead now,
        # optionally a Notification can be sent before closing
        try:
            ctxt.receive_data()
            ctxt.expect_message("Notification")
            ctxt.close()
            raise ValueError("illegal message erroneously accepted")
        except Exception as exc:
            # part 2: try the same after initial handshake
            ctxt.close()
            with create_upstream_context_with_handshake() as ctxt:
                ctxt.send_tag_and_bytes(None, illegal_msg_bytes)
                # other end has to close connection so check if socked is dead now,
                # optionally a Notification can be sent before closing
                try:
                    ctxt.receive_data()
                    ctxt.expect_message("Notification")
                    ctxt.close()
                    raise ValueError("illegal message erroneously accepted after handshake") from exc
                except:
                    pass
