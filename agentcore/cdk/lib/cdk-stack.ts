
import { AgentCoreApplication, type AgentCoreApplicationProps } from '@aws/agentcore-cdk';
import { Stack, type StackProps } from 'aws-cdk-lib';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import { Construct } from 'constructs';

export interface AgentCoreStackProps extends StackProps {
  application: AgentCoreApplicationProps;
}

export class AgentCoreStack extends Stack {
  public readonly application: AgentCoreApplication;

  constructor(scope: Construct, id: string, props: AgentCoreStackProps) {
    super(scope, id, props);

    this.application = new AgentCoreApplication(this, 'Application', props.application);

    const groqSecret = secretsmanager.Secret.fromSecretNameV2(
      this,
      'GroqApiKey',
      'lauki-finance/groq-api-key'
    );

    this.application.runtime('agent').grantRead(groqSecret);
  }
}
