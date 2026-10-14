Docker compose setup to include Keycloak as identity provider in the local development stack.

## Configuration

In general there should be one client configured per involved application, e.g. `openproject` and `nextcloud`.

Clients should usually be configured as follows:

* Client authentication: On (makes the client "confidential", i.e. requires Client ID and secret)
* Authorization: On (Needed later, to allow adding specific permissions, such as token exchange)

### Allowing to perform Token Exchange

Token exchange needs to be allowed for involved clients. We usually allow this on a per-client basis, i.e. one client (source) is generally allowed to exchange (obtain) tokens for another client (target).

Let's say we want to allow `openproject` to exchange a `nextcloud` token:

Things we need to do:
1. Define a policy that identifies clients that should be allowed to perform token exchange
    * Go to the client identifying your realm (by default `master-realm` or `realm-management`), then `Authorization` -> `Policies`
    * Create a new policy of type `Client` (i.e. the policy matches depending on the client that wants to do something)
    * Give it a suitable name (e.g. `can-exchange-nextcloud-token`) and add to clients `openproject` and all other names of clients that
      should be allowed to exchange a token for the target
    * Logic needs to remain at the default `Positive`, so that the client name _matches_ the policy
2. In the target client, specify who is allowed to exchange tokens for it
    * Go to the client that you want to exchange a token for (e.g. `nextcloud`), then `Permissions` -> `token-exchange`
    * Under policies, add the newly created `can-exchange-nextcloud-token` policy
      * By default all policies must match to allow token exchange (`Unanimous`), since we only define one policy matching
        all allowed clients, this will work fine
      * If you prefer to have one policy per client, the decision strategy would need to be `Affirmative` instead, so that one matching strategy is enough

### Adding additional audiences to tokens

An alternative way to allow a source application to obtain tokens for a target application, is to include the target application among the
audience of tokens issued to the source application from the beginning. One way to do this, is by configuring an additional scope that an
application can request, to immediately obtain the additional audience.

Let's say we want to allow `openproject` to use tokens it receives to make API calls to `nextcloud`:

1. Create a new client scope (left-hand side menu)
    * give it a desirable name (e.g. `obtain-nextcloud-audience`)
    * Set the type to `Optional` (i.e. it will have to be requested by the client explicitly)
    * Add a mapper to the client scope: `Mappers` -> `Add Mapper` -> `configure a new mapper` -> `Audience`
    * Configure it to include the audience for the target client, e.g. `nextcloud` and make sure to select `Add to access token`
2. Add client scope to client
    * `Clients` -> name of your source client (e.g. `openproject`) -> `Client scopes` -> `Add client scope` -> name of your client scope (e.g. `obtain-nextcloud-audience`)
3. Request scope in client
    * The way we configured it, no additional audiences will be added by default, your client will now have to request this scope to obtain the additional audience (making it toggleable in development from the client side)
    * In OpenProject this is done in the OIDC provider settings
