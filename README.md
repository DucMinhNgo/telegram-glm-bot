
### Telegram
```sh
/newbot
```

###Test
```sh
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "THUDM/glm-4-9b-chat",
    "messages": [
      {"role": "user", "content": "Xin chào"}
    ]
  }'
```