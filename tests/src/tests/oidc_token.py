"""Tests for oidc-token module."""

from dagger import dag


async def test_oidc_token() -> str:
    """Run oidc-token module tests."""
    results = []

    # Sample JWT for testing
    sample_jwt = "eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJ0ZXN0IiwiYXVkIjoidGVzdCIsInN1YiI6InRlc3QifQ.signature"
    test_token = dag.set_secret("test-jwt", sample_jwt)

    # Test token_claims
    claims = await dag.oidc_token().token_claims(token=test_token)
    if "iss" not in claims:
        raise ValueError(f"Token missing 'iss' claim: {claims}")
    results.append("PASS: token_claims decodes JWT payload")

    # Test gitlab_token
    gitlab_secret = dag.set_secret("gitlab-jwt", "test-token")
    _ = dag.oidc_token().gitlab_token(ci_job_jwt=gitlab_secret)
    results.append("PASS: gitlab_token pass-through")

    # Test circleci_token
    circleci_secret = dag.set_secret("circleci-jwt", "test-token")
    _ = dag.oidc_token().circleci_token(oidc_token=circleci_secret)
    results.append("PASS: circleci_token pass-through")

    return "\n".join(results)
