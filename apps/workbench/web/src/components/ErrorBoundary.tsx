import { Component, type ErrorInfo, type ReactNode } from "react";
import { Button } from "./ui/Button";
import { EmptyState } from "./ui/EmptyState";

interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<{ children: ReactNode }, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error(error, info.componentStack);
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <EmptyState title="This page stopped with an error">
        <span className="block">{this.state.error.message}</span>
        <span className="mt-3 inline-flex gap-2">
          <Button onClick={() => this.setState({ error: null })}>Try again</Button>
          <Button onClick={() => window.location.reload()}>Reload the Workbench</Button>
        </span>
      </EmptyState>
    );
  }
}
