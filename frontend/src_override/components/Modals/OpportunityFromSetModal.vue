<template>
  <Dialog
    v-model="show"
    :options="{
      title: __('Set Opportunity From'),
      size: 'md',
      actions: [
        {
          label: __('Save'),
          variant: 'solid',
          onClick: setOpportunityFrom,
        },
      ],
    }"
  >
    <template #body-content>
      <div>
        <Select
          class="form-control"
          label="Opportunity From"
          :options="[
            {
              label: 'Lead',
              value: 'Lead',
            },
            {
              label: 'Customer',
              value: 'Customer',
            },
            {
              label: 'Prospect',
              value: 'Prospect',
            },
          ]"
          v-model="_opportunityFields.opportunityFrom"
        />
      </div>
      <div class="mt-6">
        <Link
          class="form-control"
          label="Party Name"
          :value="_opportunityFields.partyName"
          :doctype="_opportunityFields.opportunityFrom"
          @change="(option) => (_opportunityFields.partyName = option)"
          :placeholder="__('Party Name')"
        >
        </Link>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, nextTick, watch, reactive } from 'vue'
import { call, Select, toast } from 'frappe-ui'
import Link from '@/components/Controls/Link.vue'

const props = defineProps({
  opportunityFrom: {
    type: Object,
    default: {
      opportunityFrom: 'Lead',
      partyName: '',
    },
  },
  docname: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['after'])

const _opportunityFields = reactive({
  opportunityFrom: '',
  partyName: '',
})

const show = defineModel()

async function setOpportunityFrom() {
  try {
    await call('frappe.client.set_value', {
      doctype: 'Opportunity',
      name: props.docname,
      fieldname: {
        opportunity_from: _opportunityFields.opportunityFrom,
        party_name: _opportunityFields.partyName,
      },
    })
    show.value = false
    toast.success(__('Opportunity Updated'))
    emit('after')
  } catch (error) {
    toast.error(error || __('Failed to update Opportunity'))
  }
}

watch(
  () => show.value,
  (value) => {
    if (!value) return
    nextTick(() => {
      _opportunityFields.opportunityFrom = props.opportunityFrom.opportunityFrom
      _opportunityFields.partyName = props.opportunityFrom.partyName
    })
  },
)
</script>
