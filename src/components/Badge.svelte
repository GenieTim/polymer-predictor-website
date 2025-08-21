<script lang="ts">
  interface Props {
    label: string;
    value: string;
    title?: string;
    variant?: "primary" | "secondary" | "success";
  }

  let { label, value, title, variant = "secondary" }: Props = $props();
</script>

<span>
  <i>{@html label}</i> = 
  <span class="badge badge-{variant}" {title}>
    {value}
  </span>
</span>
