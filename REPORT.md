### 1. Краткая информация:

- **ФИО:** Толканюк Екатерина Андреевна
- **Группа:** ФТ-304
- **Операционная система:** Windows 11 с wsl
- **Архитектура компьютера:** x86_64
- **Kubernetes-контекст:** `kind-hosting-lab`
- **Namespace:** `homework-1`

### 2. Описание приложения

Простое HTTP-приложение на Python, Flask.

Приложение слушает адрес `0.0.0.0` на порту `8000`. При GET-запросе к `/` возвращает JSON с сообщением, моим именем и булевым значением наличия токена.

Используемые переменные окружения:

| Переменная | Назначение | Источник |
|---|---|---|
| `APP_MESSAGE` | Сообщение приложения | ConfigMap |
| `APP_AUTHOR` | Мое имя | ConfigMap |
| `APP_TOKEN` | Токен приложения | Secret |

Токен не возвращается, приложение просто сообщает, настроен ли он.

Пример HTTP-ответа на практике (есть на одном из скриншотов):

```json
{
  "author":"Толканюк Катя",
  "message":"Биба и Боба",
  "tokenConfigured":true
}
```

### 3. Сборка и публикация Docker-образа

Сборка образа:

```bash
docker build --no-cache -t localhost:5001/biba-boba:v4 .
```

Публикация в локальный Registry:

```bash
docker push localhost:5001/biba-boba:v4
```

**Результат `docker push`:**

```text
The push refers to repository [localhost:5001/biba-boba]
161d130b2ff9: Pushed
a5883d972f3b: Layer already exists
5a87fe1d9224: Pushed
ecc510c1e359: Layer already exists
6f7ab96cf1ba: Pushed
48d1b5be612e: Pushed
c66e5fdb25c2: Layer already exists
bb8166eb34e6: Layer already exists
6aaf5b0aae75: Layer already exists
v4: digest: sha256:34b4878aa200d771de0f02ce273c26f7fdb157c39e7d6eda5f6e4b64b1d78d22 size: 856
```

Использованный образ: `localhost:5001/biba-boba:v4`.

v4, т.к. было пару ошибок в коде и надо было его менять :)

### 4. Развёртывание в Kubernetes

Выбор контекста:

```bash
kubectl config use-context kind-hosting-lab
```

Создание namespace:

```bash
kubectl apply -f k8s/namespace.yaml
```

Применение ConfigMap и Secret:

```bash
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
```

Применение Deployment:

```bash
kubectl apply -f k8s/deployment.yaml
```

Ожидание готовности Deployment:

```bash
kubectl -n homework-1 rollout status deployment/biba-boba --timeout=180s
```

Получение сведений о ресурсах:

```bash
kubectl -n homework-1 get deployments,replicasets,pods
```

**Фактический вывод:**

```text
NAME                        READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/biba-boba   2/2     2            2           29m

NAME                                   DESIRED   CURRENT   READY   AGE
replicaset.apps/biba-boba-595568ff85   2         2         2       9m41s
replicaset.apps/biba-boba-5c6649478d   0         0         0       21m
replicaset.apps/biba-boba-7654d66c49   0         0         0       29m
replicaset.apps/biba-boba-78c877f66    0         0         0       15m
replicaset.apps/biba-boba-c4c5df88c    0         0         0       17m

NAME                             READY   STATUS    RESTARTS   AGE
pod/biba-boba-595568ff85-7jnrp   1/1     Running   0          9m41s
pod/biba-boba-595568ff85-jn5dt   1/1     Running   0          9m40s
```

Deployment настроен на две реплики приложения.

### 5. Проверка HTTP-доступности

Запуск перенаправления портов:

```bash
kubectl -n homework-1 port-forward deployment/biba-boba 8082:8000
```

В другом терминале выполнен запрос:

```bash
curl -i http://localhost:8082/
```

**Фактический HTTP-ответ:**

```text
HTTP/1.1 200 OK
Server: Werkzeug/3.1.9 Python/3.14.8
Date: Sun, 18 Oct 2026 10:05:56 GMT
Content-Type: application/json
Content-Length: 95
Connection: close

{"author":"Толканюк Катя","message":"Биба и Боба","tokenConfigured":true}
```


### 6. Эксперимент № 1 — восстановление Pod

До удаления проверено количество Pod:

```bash
kubectl -n homework-1 get pods -o wide
```

```text
NAME                        READY   STATUS    RESTARTS   AGE   IP            NODE                        NOMINATED NODE   READINESS GATES
biba-boba-78c877f66-gb6m2   1/1     Running   0          73s   10.244.0.21   hosting-lab-control-plane   <none>           <none>
biba-boba-78c877f66-xf6vz   1/1     Running   0          72s   10.244.0.22   hosting-lab-control-plane   <none>           <none>
```

Удаление одного Pod:

```bash
kubectl -n homework-1 delete pod [ИМЯ_POD]
```

В моем случае [ИМЯ_POD] было `biba-boba-78c877f66-gb6m2`

Повторная проверка:

```bash
kubectl -n homework-1 get pods
```

```text
NAME                        READY   STATUS    RESTARTS   AGE
biba-boba-78c877f66-swtfd   1/1     Running   0          48s
biba-boba-78c877f66-xf6vz   1/1     Running   0          2m57s
```


**Наблюдения:**

До удаления работали два Pod. После удаления `biba-boba-78c877f66-gb6m2` Kubernetes создал новый Pod `biba-boba-78c877f66-swtfd`. В итоге снова работают две реплики приложения.

**Вывод:** Deployment поддерживает заданное количество реплик. Если Pod удаляется, контроллер создаёт замену, чтобы привести фактическое состояние к желаемому.

### 7. Эксперимент № 2 — изменение ConfigMap

Сначала зафиксировано исходное значение `APP_MESSAGE`.

Изменение значения `APP_MESSAGE` в `k8s/configmap.yaml`, например на:

```yaml
APP_MESSAGE: "Совершенно новые Биба и Боба"
```

Применение изменений:

```bash
kubectl apply -f k8s/configmap.yaml
```

Проверка ответа приложения до перезапуска Pod:

```bash
curl -s http://localhost:8082/
```

Перезапуск Deployment:

```bash
kubectl -n homework-1 rollout restart deployment/biba-boba
kubectl -n homework-1 rollout status deployment/biba-boba
```

Повторная проверка:

```bash
curl -s http://localhost:8082/
```

**Наблюдения:**

- Ответ до перезапуска: `{"author":"Толканюк Катя","message":"Биба и Боба","tokenConfigured":true}`
- Ответ после перезапуска: `{"author":"Толканюк Катя","message":"Совершенно новые Биба и Боба","tokenConfigured":true}`

**Вывод:** При изменении ConfigMap переменные окружения уже работающих контейнеров автоматически не обновляются. После выполнения rollout restart Kubernetes пересоздал Pod и запустил новые контейнеры, которые получили обновлённые значения переменных окружения. Пересобирать Docker-образ для изменения конфигурации не потребовалось.

### 8. Ответы на контрольные вопросы

**1. Зачем нужны labels и selector?**

`Labels` — это метки (ключ/значение), которые позволяют находить и объединять объекты.
`Selector` задаёт критерии выбора объектов по этим меткам. Например, Deployment использует `matchLabels`, чтобы определять, какими Pod он управляет. Метки также помогают фильтровать объекты при выполнении команд `kubectl`.
В Deployment метки Pod должны совпадать с matchLabels в selector, чтобы Deployment мог управлять этими Pod.

**2. Чем `requests` отличаются от `limits`?**

`requests` учитываются при размещении Pod на узле: на нём должно быть достаточно ресурсов.
`limits` ограничивают потребление ресурсов контейнером. При превышении CPU-лимита процесс может замедляться, а превышение лимита памяти может привести к `OOMKilled`.


**3. Для чего нужны ConfigMap и Secret?**

ConfigMap предназначен для хранения несекретных настроек отдельно от образа приложения.
Secret предназначен для хранения чувствительных данных, например токенов и паролей, отдельно от конфигурации приложения.

**4. Почему Base64 не защищает пароль?**

Base64 — это способ кодирования данных, а не шифрование. Закодированное значение можно восстановить без ключа, поэтому Base64 не защищает пароль или токен.

### 9. Удаление ресурсов

`kubectl delete namespace homework-1`

---

Скриншоты выполнения команд приложены в папку img