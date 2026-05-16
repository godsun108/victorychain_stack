import { createConfig, http } from "wagmi";
import { base, mainnet, polygon } from "wagmi/chains";
import { injected, walletConnect } from "wagmi/connectors";

const projectId = import.meta.env.VITE_WALLETCONNECT_PROJECT_ID ?? "";
const walletConnectOptIn = (import.meta.env.VITE_ENABLE_WALLETCONNECT ?? "false").toLowerCase() === "true";

const connectors = projectId && walletConnectOptIn
  ? [
      injected(),
      walletConnect({
        projectId,
        showQrModal: true,
        metadata: {
          name: "Victory Foundation Impact Portal",
          description: "Choose where compassion flows.",
          url: "https://victory.foundation",
          icons: ["https://victory.foundation/icon.png"]
        }
      })
    ]
  : [injected()];

export const walletConfig = createConfig({
  chains: [mainnet, base, polygon],
  connectors: connectors as any,
  transports: {
    [mainnet.id]: http(),
    [base.id]: http(),
    [polygon.id]: http()
  }
});

export const walletConnectEnabled = Boolean(projectId && walletConnectOptIn);
