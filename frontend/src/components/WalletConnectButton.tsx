import React from "react";
import { useAccount, useConnect, useDisconnect } from "wagmi";

import { walletConnectEnabled } from "../lib/wallet";

export function WalletConnectButton() {
  const [open, setOpen] = React.useState(false);
  const { address, chain, isConnected } = useAccount();
  const { connect, connectors, error, isPending, variables } = useConnect();
  const { disconnect } = useDisconnect();

  React.useEffect(() => {
    if (!open) return;
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [open]);

  const shortAddress = address ? `${address.slice(0, 6)}...${address.slice(-4)}` : "Not connected";

  return (
    <>
      <button className="wallet-trigger" type="button" onClick={() => setOpen(true)}>
        {isConnected ? `Wallet: ${shortAddress}` : "Connect Wallet"}
      </button>

      {open && (
        <div className="wallet-modal-backdrop" onClick={() => setOpen(false)}>
          <div className="wallet-modal" onClick={(event) => event.stopPropagation()}>
            <div className="wallet-modal-header">
              <strong>Wallet Connection</strong>
              <button className="wallet-close" type="button" onClick={() => setOpen(false)} aria-label="Close">
                ×
              </button>
            </div>

            {isConnected ? (
              <div className="wallet-state">
                <div>Connected: {shortAddress}</div>
                <div>Network: {chain?.name ?? "Unknown"}</div>
                <button
                  className="wallet-action danger"
                  type="button"
                  onClick={() => {
                    disconnect();
                    setOpen(false);
                  }}
                >
                  Disconnect
                </button>
              </div>
            ) : (
              <div className="wallet-list">
                {connectors.map((connector, index) => {
                  const c = connector as any;
                  const connectorKey = c.uid ?? c.id ?? `connector-${index}`;
                  const connectorName = c.name ?? c.id ?? `Connector ${index + 1}`;
                  const pendingId = (variables?.connector as any)?.uid ?? (variables?.connector as any)?.id;
                  return (
                    <button
                      className="wallet-action"
                      type="button"
                      key={connectorKey}
                      onClick={() => connect({ connector })}
                      disabled={isPending}
                    >
                      {isPending && pendingId === connectorKey ? `Connecting ${connectorName}...` : connectorName}
                    </button>
                  );
                })}
                {!walletConnectEnabled && (
                  <small className="wallet-note">WalletConnect disabled: set `VITE_WALLETCONNECT_PROJECT_ID`.</small>
                )}
              </div>
            )}

            {error && <small className="wallet-error">{error.message}</small>}
          </div>
        </div>
      )}
    </>
  );
}
