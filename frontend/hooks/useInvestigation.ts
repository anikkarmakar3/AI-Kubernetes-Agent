import { useMutation } from "@tanstack/react-query";

import { investigateCluster } from "@/services/api";

export function useInvestigation() {
  return useMutation({ mutationFn: ({ context, token }: { context?: string; token?: string }) => investigateCluster(context, token) });
}
