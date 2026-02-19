from aws_cdk import Stack, aws_cognito as cognito
from constructs import Construct

class AuthStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, env_name: str, domain_prefix: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        self.user_pool = cognito.UserPool(
            self,
            "OrdersUserPool", 
            user_pool_name=f"orders-userpool-{env_name}",
            self_sign_up_enabled=False,
            sign_in_aliases=cognito.SignInAliases(email=True),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
        )

        # Hosted UI requires OAuth settings on the app client
        self.app_client = self.user_pool.add_client(
            "OrdersAppClient",
            user_pool_client_name=f"orders-appclient-{env_name}",
            generate_secret=False,
            auth_flows=cognito.AuthFlow(user_password=True, user_srp=True),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    authorization_code_grant=True,
                ),
                scopes=[cognito.OAuthScope.OPENID, cognito.OAuthScope.EMAIL],
                callback_urls=["http://localhost:3000/callback"],
                logout_urls=["http://localhost:3000/logout"],
            ),
        )

        # Domain for Hosted UI (default Cognito domain using prefix)
        self.user_pool.add_domain(
            "OrdersDomain",
            cognito_domain=cognito.CognitoDomainOptions(domain_prefix=domain_prefix),
        )
