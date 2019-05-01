curl --header "Content-Type: application/json" \
  --request POST \
  --data '{"hash": "21e0b13a6f61d42fc9d92b166f36a8d2e6d7a5f0dc7d76fd580e71df94d7d7d7d036153b7bbd248a4591cb06cd6f4fcca0e79a1d981b1d96dbedc3e438234f8d", "signature": "832510c0188dcd7db95bbad359cc0251504405413c31a495724444762f0da37df443cff3628d6f8bee86a15a64a92094431bf36ae7d6d35012b3345c3e6e7205"}' \
  http://localhost:5000/api/crypto/verify

