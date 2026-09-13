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

        # 2. Connect Bob to room_a
        with client.websocket_connect(f"/ws/chat/{room_a}?sender_name=Bob") as ws_bob:
            # Bob receives history first
            history_event = ws_bob.receive_json()
            assert history_event["type"] == "history"
            assert len(history_event["messages"]) >= 1

            # Bob receives "Bob joined the chat"
            bob_join = ws_bob.receive_json()
            assert bob_join["type"] == "system"
            assert "Bob joined" in bob_join["text"]

            # Alice also receives "Bob joined the chat"
            alice_saw_bob = ws_alice.receive_json()
            assert alice_saw_bob["type"] == "system"
            assert "Bob joined" in alice_saw_bob["text"]

            # 3. Alice sends message in room_a
            ws_alice.send_text(json.dumps({
                "sender_name": "Alice",
                "text": "Hi Bob, how can I help you today?"
            }))

            # Both Alice and Bob should receive Alice's message
            msg_for_alice = ws_alice.receive_json()
            assert msg_for_alice["text"] == "Hi Bob, how can I help you today?"
            assert msg_for_alice["sender_name"] == "Alice"

            msg_for_bob = ws_bob.receive_json()
            assert msg_for_bob["text"] == "Hi Bob, how can I help you today?"
            assert msg_for_bob["sender_name"] == "Alice"

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


if __name__ == "__main__":
    test_system_endpoints()
    test_customer_crud()
    test_account_crud()
    test_payment_crud()
    test_account_activity_crud()
    test_risk_feature_crud_and_early_warning()
    test_cascade_delete()
    test_websocket_chat_rooms()
    print("\n🎉 ALL TESTS PASSED SUCCESSFULLY!")

