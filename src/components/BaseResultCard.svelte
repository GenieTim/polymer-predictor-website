<script lang="ts">
  import newGithubIssueUrl from "new-github-issue-url";
  import type { Snippet } from "svelte";

  interface Props {
    title: string;
    loading: boolean;
    dirty: boolean;
    loadingText?: string;
    emptyText?: string;
    hasResult: boolean;
    error?: string | null;
    id?: string;
    children: Snippet;
  }

  let {
    title,
    loading,
    dirty,
    loadingText = "Computing...",
    emptyText = "Results will appear here.",
    hasResult,
    error = null,
    id,
    children,
  }: Props = $props();

  let errorUrl = $derived(
    newGithubIssueUrl({
      user: "GenieTim",
      repo: "polymer-predictor-website",
      title: `Error in ${title}`,
      body: `An error occurred:\n\n\`\`\`\n${error}\n\`\`\``,
    })
  );
</script>

<div {id} class:not-current={dirty} class="prediction">
  <div class="card">
    <div class="card-header">
      <div class="row">
        <div class="col">
          <h5 class="card-title mb-0">{title}</h5>
        </div>
        {#if loading && hasResult}
          <div class="col align-right text-end">
            <small class="text-muted badge badge-warning">Refining...</small>
          </div>
        {/if}
      </div>
    </div>
    <div class="card-body">
      {#if error}
        <div class="alert alert-danger">
          <i class="fas fa-exclamation-triangle"></i>
          <strong>Error:</strong>
          {error}
          <a href={errorUrl} class="btn btn-link">Report Issue</a>
        </div>
      {:else if loading && !hasResult}
        <p>{loadingText}</p>
      {:else if hasResult}
        {@render children()}
        {#if loading}
          <p class="mt-2 text-muted">Refining...</p>
        {/if}
      {:else}
        <p>{emptyText}</p>
      {/if}
    </div>
  </div>
</div>

<style>
  .not-current {
    opacity: 0.5;
    filter: grayscale(40%);
  }
</style>
