import uuid
from datetime import date
from fastapi.testclient import TestClient

from main import app
from database import init_db

init_db()
client = TestClient(app)


def test_system_endpoints():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert "message" in data
    assert data["version"] == "1.0.0"

    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "database": "connected"}
    print("✓ System endpoints passed")


def test_customer_crud():
    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "full_name": "Jane Doe",
        "email": unique_email,
        "age": 32,
        "region": "West",
        "employment_status": "employed",
        "income_bracket": "75k-100k",
        "tenure_months": 24,
        "credit_score": 720,
    }

    # 1. Create
    res = client.post("/customers", json=payload)
    assert res.status_code == 201, res.text
    customer = res.json()
    customer_id = customer["id"]
    assert customer["email"] == unique_email
    assert customer["full_name"] == "Jane Doe"
    assert customer["credit_score"] == 720

    # Duplicate email check
    res_dup = client.post("/customers", json=payload)
    assert res_dup.status_code == 409

    # 2. Read (single)
    res = client.get(f"/customers/{customer_id}")
    assert res.status_code == 200
    assert res.json()["id"] == customer_id

    # 404 for non-existent
    res_404 = client.get(f"/customers/{uuid.uuid4()}")
    assert res_404.status_code == 404

    # 3. List with filtering
    res = client.get("/customers", params={"email": unique_email})
    assert res.status_code == 200
    customers_list = res.json()
    assert len(customers_list) == 1
    assert customers_list[0]["id"] == customer_id

    # 4. Update (PUT and PATCH)
    updated_email = f"updated_{uuid.uuid4().hex[:8]}@example.com"
    res = client.put(
        f"/customers/{customer_id}",
        json={"full_name": "Jane Smith", "email": updated_email, "credit_score": 740},
    )
    assert res.status_code == 200
    assert res.json()["full_name"] == "Jane Smith"
    assert res.json()["email"] == updated_email
    assert res.json()["credit_score"] == 740
    assert res.json()["age"] == 32  # Unmodified remains intact

    # 5. Delete
    res = client.delete(f"/customers/{customer_id}")
    assert res.status_code == 204

    # Confirm deletion
    res = client.get(f"/customers/{customer_id}")
    assert res.status_code == 404
    print("✓ Customer CRUD passed")


def test_account_crud():
    # Setup customer
    c_res = client.post(
        "/customers",
        json={"full_name": "Account Owner", "email": f"acct_{uuid.uuid4().hex[:8]}@test.com"},
    )
    assert c_res.status_code == 201
    customer_id = c_res.json()["id"]

    # 1. Create account with bad customer_id
    bad_res = client.post(
        "/accounts",
        json={
            "customer_id": str(uuid.uuid4()),
            "product_type": "personal_loan",
            "principal_amount": 5000.0,
            "interest_rate": 0.085,
        },
    )
    assert bad_res.status_code == 400

    # 1. Create account
    res = client.post(
        "/accounts",
        json={
            "customer_id": customer_id,
            "product_type": "personal_loan",
            "principal_amount": 10000.0,
            "interest_rate": 0.075,
            "total_installments": 36,
        },
    )
    assert res.status_code == 201, res.text
    account = res.json()
    account_id = account["id"]
    assert account["customer_id"] == customer_id
    assert account["product_type"] == "personal_loan"
    assert account["is_active"] is True

    # 2. Read single
    res = client.get(f"/accounts/{account_id}")
    assert res.status_code == 200
    assert res.json()["id"] == account_id

    # 3. List accounts
    res = client.get("/accounts", params={"customer_id": customer_id})
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # List customer accounts
    res = client.get(f"/customers/{customer_id}/accounts")
    assert res.status_code == 200
    assert len(res.json()) == 1

    # 4. Update
    res = client.patch(
        f"/accounts/{account_id}",
        json={"is_active": False, "interest_rate": 0.065},
    )
    assert res.status_code == 200
    assert res.json()["is_active"] is False
    assert res.json()["interest_rate"] == 0.065

    # 5. Delete
    res = client.delete(f"/accounts/{account_id}")
    assert res.status_code == 204

    res = client.get(f"/accounts/{account_id}")
    assert res.status_code == 404

    # Cleanup customer
    client.delete(f"/customers/{customer_id}")
    print("✓ Account CRUD passed")


def test_payment_crud():
    # Setup customer and account
    c_res = client.post(
        "/customers",
        json={"full_name": "Payee User", "email": f"payee_{uuid.uuid4().hex[:8]}@test.com"},
    )
    customer_id = c_res.json()["id"]

    a_res = client.post(
        "/accounts",
        json={
            "customer_id": customer_id,
            "product_type": "credit_card",
            "principal_amount": 3000.0,
            "interest_rate": 0.199,
        },
    )
    account_id = a_res.json()["id"]

    # 1. Create payment with bad account_id
    bad_res = client.post(
        "/payments",
        json={
            "account_id": str(uuid.uuid4()),
            "amount_due": 150.0,
            "due_date": "2026-10-01",
        },
    )
    assert bad_res.status_code == 400

    # 1. Create payment
    res = client.post(
        "/payments",
        json={
            "account_id": account_id,
            "amount_due": 250.0,
            "amount_paid": 250.0,
            "currency": "USD",
            "due_date": "2026-10-01",
            "payment_date": "2026-10-01",
            "status": "on_time",
            "payment_method": "auto_debit",
            "channel": "app",
            "installment_number": 1,
        },
    )
    assert res.status_code == 201, res.text
    payment = res.json()
    payment_id = payment["id"]
    assert payment["account_id"] == account_id
    assert payment["amount_due"] == 250.0
    assert payment["status"] == "on_time"

    # 2. Read single
    res = client.get(f"/payments/{payment_id}")
    assert res.status_code == 200
    assert res.json()["id"] == payment_id

    # 3. List payments
    res = client.get("/payments", params={"account_id": account_id})
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # List account payments
    res = client.get(f"/accounts/{account_id}/payments")
    assert res.status_code == 200
    assert len(res.json()) == 1

    # 4. Update
    res = client.patch(
        f"/payments/{payment_id}",
        json={"days_late": 5, "status": "late", "late_fee_charged": 25.0},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "late"
    assert res.json()["days_late"] == 5
    assert res.json()["late_fee_charged"] == 25.0

    # 5. Delete
    res = client.delete(f"/payments/{payment_id}")
    assert res.status_code == 204

    res = client.get(f"/payments/{payment_id}")
    assert res.status_code == 404

    # Cleanup
    client.delete(f"/customers/{customer_id}")
    print("✓ Payment CRUD passed")


def test_account_activity_crud():
    # Setup customer
    c_res = client.post(
        "/customers",
        json={"full_name": "Activity User", "email": f"act_{uuid.uuid4().hex[:8]}@test.com"},
    )
    customer_id = c_res.json()["id"]

    # 1. Create activity with bad customer
    bad_res = client.post(
        "/account-activity",
        json={
            "customer_id": str(uuid.uuid4()),
            "snapshot_date": "2026-09-01",
        },
    )
    assert bad_res.status_code == 400

    # 1. Create
    res = client.post(
        "/account-activity",
        json={
            "customer_id": customer_id,
            "snapshot_date": "2026-09-01",
            "checking_balance": 1500.50,
            "savings_balance": 5000.0,
            "overdraft_count_30d": 1,
            "large_withdrawal_flag": False,
            "salary_deposit_detected": True,
            "app_logins_30d": 12,
            "support_contacts_30d": 2,
            "hardship_flag": False,
        },
    )
    assert res.status_code == 201, res.text
    activity = res.json()
    activity_id = activity["id"]
    assert activity["customer_id"] == customer_id
    assert activity["checking_balance"] == 1500.50

    # 2. Read single
    res = client.get(f"/account-activity/{activity_id}")
    assert res.status_code == 200
    assert res.json()["id"] == activity_id

    # 3. List activities
    res = client.get("/account-activity", params={"customer_id": customer_id})
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # List customer activities
    res = client.get(f"/customers/{customer_id}/account-activity")
    assert res.status_code == 200
    assert len(res.json()) == 1

    # 4. Update
    res = client.patch(
        f"/account-activity/{activity_id}",
        json={"hardship_flag": True, "support_contacts_30d": 5},
    )
    assert res.status_code == 200
    assert res.json()["hardship_flag"] is True
    assert res.json()["support_contacts_30d"] == 5

    # 5. Delete
    res = client.delete(f"/account-activity/{activity_id}")
    assert res.status_code == 204

    res = client.get(f"/account-activity/{activity_id}")
    assert res.status_code == 404

    # Cleanup
    client.delete(f"/customers/{customer_id}")
    print("✓ Account Activity CRUD passed")


def test_risk_feature_crud_and_early_warning():
    # Setup customer
    c_res = client.post(
        "/customers",
        json={"full_name": "Risk User", "email": f"risk_{uuid.uuid4().hex[:8]}@test.com"},
    )
    customer_id = c_res.json()["id"]

    # Early warning on customer with no data -> 404
    ew_404 = client.get(f"/customers/{customer_id}/early-warning")
    assert ew_404.status_code == 404

    # 1. Create risk feature
    res = client.post(
        "/risk-features",
        json={
            "customer_id": customer_id,
            "as_of_date": "2026-09-10",
            "consecutive_partial_payments": 2,
            "missed_payment_streak": 1,
            "avg_days_late_90d": 14.5,
            "debt_to_income_ratio": 0.42,
            "credit_utilization_pct": 78.5,
            "balance_trend_30d": -0.15,
            "early_warning_flag": True,
            "defaulted": False,
        },
    )
    assert res.status_code == 201, res.text
    feature = res.json()
    feature_id = feature["id"]
    assert feature["customer_id"] == customer_id
    assert feature["early_warning_flag"] is True
    assert feature["credit_utilization_pct"] == 78.5

    # 2. Read single
    res = client.get(f"/risk-features/{feature_id}")
    assert res.status_code == 200
    assert res.json()["id"] == feature_id

    # 3. List risk features
    res = client.get("/risk-features", params={"customer_id": customer_id})
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # List customer risk features
    res = client.get(f"/customers/{customer_id}/risk-features")
    assert res.status_code == 200
    assert len(res.json()) == 1

    # 4. Check early-warning status
    ew_res = client.get(f"/customers/{customer_id}/early-warning")
    assert ew_res.status_code == 200
    ew_data = ew_res.json()
    assert ew_data["early_warning_flag"] is True
    assert ew_data["consecutive_partial_payments"] == 2
    assert ew_data["missed_payment_streak"] == 1
    assert ew_data["debt_to_income_ratio"] == 0.42

    # 5. Update
    res = client.patch(
        f"/risk-features/{feature_id}",
        json={"defaulted": True, "days_to_default": 15},
    )
    assert res.status_code == 200
    assert res.json()["defaulted"] is True
    assert res.json()["days_to_default"] == 15

    # 6. Delete
    res = client.delete(f"/risk-features/{feature_id}")
    assert res.status_code == 204

    res = client.get(f"/risk-features/{feature_id}")
    assert res.status_code == 404

    # Cleanup
    client.delete(f"/customers/{customer_id}")
    print("✓ Risk Feature CRUD passed")


def test_cascade_delete():
    # Create customer -> account -> payment & activity & risk feature
    c_res = client.post(
        "/customers",
        json={"full_name": "Cascade User", "email": f"casc_{uuid.uuid4().hex[:8]}@test.com"},
    )
    customer_id = c_res.json()["id"]

    a_res = client.post(
        "/accounts",
        json={
            "customer_id": customer_id,
            "product_type": "mortgage",
            "principal_amount": 250000.0,
            "interest_rate": 0.045,
        },
    )
    account_id = a_res.json()["id"]

    p_res = client.post(
        "/payments",
        json={
            "account_id": account_id,
            "amount_due": 1400.0,
            "due_date": "2026-10-01",
        },
    )
    payment_id = p_res.json()["id"]

    act_res = client.post(
        "/account-activity",
        json={
            "customer_id": customer_id,
            "snapshot_date": "2026-09-01",
        },
    )
    activity_id = act_res.json()["id"]

    rf_res = client.post(
        "/risk-features",
        json={
            "customer_id": customer_id,
            "as_of_date": "2026-09-01",
        },
    )
    risk_id = rf_res.json()["id"]

    # Delete customer - should cascade delete account, payment, activity, and risk feature
    del_res = client.delete(f"/customers/{customer_id}")
    assert del_res.status_code == 204

    # Verify all child entities are deleted
    assert client.get(f"/customers/{customer_id}").status_code == 404
    assert client.get(f"/accounts/{account_id}").status_code == 404
    assert client.get(f"/payments/{payment_id}").status_code == 404
    assert client.get(f"/account-activity/{activity_id}").status_code == 404
    assert client.get(f"/risk-features/{risk_id}").status_code == 404
    print("✓ Cascade delete verification passed")


def test_websocket_chat_rooms():
    import json

    room_a = f"room_a_{uuid.uuid4().hex[:6]}"
    room_b = f"room_b_{uuid.uuid4().hex[:6]}"

    # 1. Connect Alice to room_a
    with client.websocket_connect(f"/ws/chat/{room_a}?sender_name=Alice") as ws_alice:
        # Alice receives "Alice joined the chat"
        msg = ws_alice.receive_json()
        assert msg["type"] == "system"
        assert "Alice joined" in msg["text"]

        # Alice sends message in room_a
        ws_alice.send_text(json.dumps({
            "sender_name": "Alice",
            "text": "Hi Bob, how can I help you today?"
        }))
        msg_for_alice = ws_alice.receive_json()
        assert msg_for_alice["text"] == "Hi Bob, how can I help you today?"
        assert msg_for_alice["sender_name"] == "Alice"

        # 2. Connect Bob to room_a
        with client.websocket_connect(f"/ws/chat/{room_a}?sender_name=Bob") as ws_bob:
            # Bob receives dialogue history first (containing Alice's message, but NO join/leave presence events)
            history_event = ws_bob.receive_json()
            assert history_event["type"] == "history"
            assert len(history_event["messages"]) == 1
            assert history_event["messages"][0]["text"] == "Hi Bob, how can I help you today?"
            assert all(m["type"] == "message" for m in history_event["messages"])

            # Bob receives "Bob joined the chat"
            bob_join = ws_bob.receive_json()
            assert bob_join["type"] == "system"
            assert "Bob joined" in bob_join["text"]

            # Alice also receives "Bob joined the chat"
            alice_saw_bob = ws_alice.receive_json()
            assert alice_saw_bob["type"] == "system"
            assert "Bob joined" in alice_saw_bob["text"]

            # 3. Bob sends a reply in room_a
            ws_bob.send_text(json.dumps({
                "sender_name": "Bob",
                "text": "Thanks Alice, I have a question about my installment."
            }))

            # Both Alice and Bob should receive Bob's message
            bob_reply_alice = ws_alice.receive_json()
            assert bob_reply_alice["text"] == "Thanks Alice, I have a question about my installment."
            assert bob_reply_alice["sender_name"] == "Bob"

            bob_reply_bob = ws_bob.receive_json()
            assert bob_reply_bob["text"] == "Thanks Alice, I have a question about my installment."
            assert bob_reply_bob["sender_name"] == "Bob"


            # 4. Multi-room isolation: Connect Charlie to room_b
            with client.websocket_connect(f"/ws/chat/{room_b}?sender_name=Charlie") as ws_charlie:
                charlie_join = ws_charlie.receive_json()
                assert charlie_join["type"] == "system"

                # Charlie sends a message in room_b
                ws_charlie.send_text("Hello Room B only!")
                charlie_msg = ws_charlie.receive_json()
                assert charlie_msg["text"] == "Hello Room B only!"

                # 5. REST message injection into room_a
                inject_res = client.post(
                    f"/chat/rooms/{room_a}/messages",
                    json={"sender_name": "Debt Alert Bot", "text": "Reminder: payment due in 3 days"},
                )
                assert inject_res.status_code == 201

                # Alice and Bob in room_a receive the injected alert
                bot_msg_alice = ws_alice.receive_json()
                assert bot_msg_alice["sender_name"] == "Debt Alert Bot"
                assert "payment due" in bot_msg_alice["text"]

                bot_msg_bob = ws_bob.receive_json()
                assert bot_msg_bob["sender_name"] == "Debt Alert Bot"

    # 6. Verify REST room and message endpoints
    rooms_res = client.get("/chat/rooms")
    assert rooms_res.status_code == 200

    messages_res = client.get(f"/chat/rooms/{room_a}/messages")
    assert messages_res.status_code == 200
    room_a_messages = messages_res.json()
    assert len(room_a_messages) >= 3
    assert any(m["sender_name"] == "Debt Alert Bot" for m in room_a_messages)

    # 7. Verify WhatsApp HTML UI endpoint
    ui_res = client.get(f"/chat/{room_a}")
    assert ui_res.status_code == 200
    assert "WhatsApp Chat Simulator" in ui_res.text
    assert room_a in ui_res.text
    print("✓ WebSocket chat rooms and multi-room simulation passed")


def test_risk_reminders_and_customer_websocket():
    import json

    # 1. Test candidates endpoint
    res = client.get("/risk-reminders/candidates")
    assert res.status_code == 200
    candidates = res.json()
    assert len(candidates) > 0
    candidate = candidates[0]
    assert "customer_id" in candidate
    assert "amount_due" in candidate
    assert "due_date" in candidate

    # 2. Test send reminder endpoint
    send_res = client.post(
        "/risk-reminders/send",
        json={
            "customer_id": candidate["customer_id"],
            "language": "es",
        },
    )
    assert send_res.status_code == 201
    send_data = send_res.json()
    assert send_data["success"] is True
    assert "conversation_id" in send_data
    assert "message" in send_data
    assert len(send_data["message"]["content"]) > 0

    # 3. Test customer websocket room persistence
    cust_id = candidate["customer_id"]
    with client.websocket_connect(f"/ws/chat/{cust_id}?sender_name=Customer") as ws:
        hist_event = ws.receive_json()
        assert hist_event["type"] == "history"
        assert len(hist_event["messages"]) >= 1

        join_msg = ws.receive_json()
        assert join_msg["type"] == "system"

        # Send customer message over WebSocket
        test_text = "Recibido, gracias por el aviso."
        ws.send_text(json.dumps({"text": test_text, "sender_name": "Customer"}))
        echo_msg = ws.receive_json()
        assert echo_msg["text"] == test_text

        # Assistant responds with supportive message
        asst_reply = ws.receive_json()
        assert asst_reply["sender_name"] == "Payment Assistant"
        assert len(asst_reply["text"]) > 0

    # 4. Verify message was persisted into DB conversation
    conv_res = client.get("/conversations", params={"customer_id": cust_id})
    assert conv_res.status_code == 200
    customer_convos = conv_res.json()
    assert len(customer_convos) >= 1
    assert customer_convos[0]["message_count"] >= 2

    print("✓ Risk reminders and customer WebSocket persistence passed")


def test_guardrails_rejection_and_distress_escalation():
    import json

    # 1. Verify that prohibited operator threat in POST /risk-reminders/send is rejected with 400
    res = client.get("/risk-reminders/candidates")
    assert res.status_code == 200
    candidates = res.json()
    assert len(candidates) > 0
    candidate = candidates[0]
    cust_id = candidate["customer_id"]

    illegal_reminder_res = client.post(
        "/risk-reminders/send",
        json={
            "customer_id": cust_id,
            "custom_message": "Te vamos a demandar en los tribunales y embargar tus bienes si no pagas de inmediato.",
        },
    )
    assert illegal_reminder_res.status_code == 400
    assert "violates fair debt collection guardrails" in illegal_reminder_res.json()["detail"]

    # 2. Verify prohibited message injection in POST /chat/rooms/{room_id}/messages is rejected with 400
    illegal_inject_res = client.post(
        f"/chat/rooms/{cust_id}/messages",
        json={
            "sender_name": "Collections Officer",
            "text": "Vamos a reportarte al buró de crédito y manchar tu historial.",
        },
    )
    assert illegal_inject_res.status_code == 400
    assert "violates fair debt collection guardrails" in illegal_inject_res.json()["detail"]

    # 3. Test WebSocket distress detection and automated empathetic specialist escalation
    with client.websocket_connect(f"/ws/chat/{cust_id}?sender_name=Customer") as ws:
        # Drain initial history and join system messages
        ws.receive_json()
        ws.receive_json()

        distress_text = "Lamentablemente perdí mi empleo y no tengo dinero para pagar la cuota este mes."
        ws.send_text(json.dumps({"text": distress_text, "sender_name": "Customer"}))

        # 1st received message: customer message echo
        echo_msg = ws.receive_json()
        assert echo_msg["text"] == distress_text

        # 2nd received message: automated empathetic assistant escalation reply
        asst_escalation_msg = ws.receive_json()
        assert asst_escalation_msg["sender_name"] == "Payment Assistant"
        assert "especialista de nuestro equipo de apoyo financiero" in asst_escalation_msg["text"]

    # 4. Verify conversation is marked is_escalated=True in the database
    conv_res = client.get("/conversations", params={"customer_id": cust_id})
    assert conv_res.status_code == 200
    convos = conv_res.json()
    assert len(convos) >= 1
    escalated_convo = convos[0]
    assert escalated_convo["is_escalated"] is True

    # 5. Verify the customer message was flagged for hardship
    msgs_res = client.get(f"/conversations/{escalated_convo['id']}/messages")
    assert msgs_res.status_code == 200
    msgs = msgs_res.json()
    assert any(m["content"] == distress_text and m["flagged"] is True for m in msgs)
    assert any("especialista de nuestro equipo de apoyo financiero" in m["content"] for m in msgs)

    # 6. Verify regulatory compliance audit milestones were logged in conversation_events table
    events_res = client.get(f"/conversations/{escalated_convo['id']}/events")
    assert events_res.status_code == 200
    events = events_res.json()
    assert len(events) >= 2
    event_types = [e["event_type"] for e in events]
    assert "customer_distress_detected" in event_types
    assert "conversation_escalated" in event_types
    assert "specialist_handoff" in event_types
    assert any(e["event_type"] == "risk_reminder_triggered" for e in events)

    # 7. Verify conversation record metadata has escalation timestamp and reason
    assert escalated_convo.get("escalated_at") is not None
    assert "Distress detected" in (escalated_convo.get("escalation_reason") or "")
    assert escalated_convo.get("event_count", 0) >= 3

    # 8. Verify the Message table strictly contains dialogue turns and NEVER transient presence events
    assert all("joined the chat" not in m["content"] for m in msgs)
    assert all("left the chat" not in m["content"] for m in msgs)
    assert all(m["role"] in ("user", "assistant") for m in msgs)

    # 9. Verify off-topic query (e.g. cake recipe, LaTeX, coding) is intercepted with polite banking redirection
    with client.websocket_connect(f"/ws/chat/{cust_id}?sender_name=Customer") as ws:
        ws.receive_json()
        ws.receive_json()

        off_topic_q = "¿Cómo puedo preparar una torta de chocolate y hornear galletas?"
        ws.send_text(json.dumps({"text": off_topic_q, "sender_name": "Customer"}))

        echo_msg = ws.receive_json()
        assert echo_msg["text"] == off_topic_q

        redirect_msg = ws.receive_json()
        assert redirect_msg["sender_name"] == "Payment Assistant"
        assert "Bancobranza" in redirect_msg["text"]
        assert "cuota" in redirect_msg["text"]

    # 10. Verify audit event for off-topic interception was recorded in conversation_events
    events_res = client.get(f"/conversations/{escalated_convo['id']}/events")
    events = events_res.json()
    assert any(e["event_type"] == "guardrail_violation_blocked" for e in events)

    print("✓ Guardrails operator rejection, distress escalation, off-topic defense, and compliance audit events passed")


def test_voice_interrupt():
    # 1. Create a test customer
    unique_email = f"voice_int_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "full_name": "Carlos Interruption",
        "email": unique_email,
        "age": 35,
        "region": "Central",
        "employment_status": "employed",
        "income_bracket": "50k-75k",
        "tenure_months": 12,
        "credit_score": 680,
    }
    res = client.post("/customers", json=payload)
    assert res.status_code == 201
    cust_id = res.json()["id"]

    # 2. Call greeting to generate an initial assistant message in the conversation
    greet_res = client.get(f"/voice/greeting/{cust_id}")
    assert greet_res.status_code == 200

    # 3. Post interruption
    int_res = client.post("/voice/interrupt", json={"customer_id": cust_id})
    assert int_res.status_code == 200
    assert int_res.json()["status"] == "interrupted"

    # 4. Verify message content updated with [interrumpido]
    conv_res = client.get("/conversations", params={"customer_id": cust_id})
    assert conv_res.status_code == 200
    conv_id = conv_res.json()[0]["id"]
    msgs_res = client.get(f"/conversations/{conv_id}/messages")
    assert msgs_res.status_code == 200
    msgs = msgs_res.json()
    assert len(msgs) >= 1
    last_asst_msg = next(m for m in reversed(msgs) if m["role"] == "assistant")
    assert "[interrumpido]" in last_asst_msg["content"]

    # 5. Calling again is idempotent (returns noop, doesn't duplicate tag)
    int_res_2 = client.post("/voice/interrupt", json={"customer_id": cust_id})
    assert int_res_2.status_code == 200
    assert int_res_2.json()["status"] == "noop"

    # 6. 404 for non-existent customer
    bad_res = client.post("/voice/interrupt", json={"customer_id": str(uuid.uuid4())})
    assert bad_res.status_code == 404

    print("✓ Voice interruption endpoint passed")


def test_voice_agent_reply_and_tone_adaptation():
    """Verify that /voice/greeting and /voice/agent-reply compute and return dynamic tone profiles."""
    cust_email = f"tone.test.{uuid.uuid4().hex[:6]}@example.com"
    payload = {
        "full_name": "Valeria Vulnerable",
        "email": cust_email,
        "credit_score": 580,
        "employment_status": "unemployed",
    }
    res = client.post("/customers", json=payload)
    assert res.status_code == 201
    cust_id = res.json()["id"]

    # 1. Greeting returns tone_profile reflecting behavioral priors
    greet_res = client.get(f"/voice/greeting/{cust_id}")
    assert greet_res.status_code == 200
    greet_data = greet_res.json()
    assert "tone_profile" in greet_data
    assert greet_data["tone_profile"]["customer_tone"] == "anxious_hardship"
    assert greet_data["tone_profile"]["playback_rate"] == 0.92
    assert "0.92x" in greet_data["tone_profile"]["pacing_label_es"]

    # 2. Agent reply with anxious customer utterance adapts voice to empathetic soothing
    reply_res = client.post(
        "/voice/agent-reply",
        json={
            "customer_id": cust_id,
            "message": "No tengo dinero ahora, estoy muy angustiada con mis deudas",
            "arousal": 0.75,
            "valence": 0.20,
            "emotion_label": "distressed",
        },
    )
    assert reply_res.status_code == 200
    reply_data = reply_res.json()
    assert "reply" in reply_data
    assert "tone_profile" in reply_data
    assert reply_data["tone_profile"]["customer_tone"] == "anxious_hardship"
    assert reply_data["tone_profile"]["ai_tone"] == "empathetic_soothing"
    assert reply_data["tone_profile"]["playback_rate"] == 0.92

    # 3. Agent reply with cooperative utterance adapts voice to collaborative efficient
    coop_res = client.post(
        "/voice/agent-reply",
        json={
            "customer_id": cust_id,
            "message": "Sí claro, quiero pagar hoy mismo por transferencia, muchas gracias",
            "arousal": 0.30,
            "valence": 0.60,
            "emotion_label": "calm",
        },
    )
    assert coop_res.status_code == 200
    coop_data = coop_res.json()
    assert coop_data["tone_profile"]["customer_tone"] == "cooperative_receptive"
    assert coop_data["tone_profile"]["ai_tone"] == "collaborative_efficient"
    assert coop_data["tone_profile"]["playback_rate"] == 1.03

    print("✓ Voice agent reply and tone adaptation endpoint passed")


if __name__ == "__main__":
    test_system_endpoints()
    test_customer_crud()
    test_account_crud()
    test_payment_crud()
    test_account_activity_crud()
    test_risk_feature_crud_and_early_warning()
    test_cascade_delete()
    test_websocket_chat_rooms()
    test_risk_reminders_and_customer_websocket()
    test_guardrails_rejection_and_distress_escalation()
    test_voice_interrupt()
    test_voice_agent_reply_and_tone_adaptation()
    print("\n🎉 ALL TESTS PASSED SUCCESSFULLY!")



