
export const multiselect = () => {
 return {
   options: [
     {
       value: 1,
       text: 'Ignacio Grondona',
       selected: false
     },
     {
       value: 2,
       text: 'Santiago Calvo',
       selected: false
     }
   ],
   selected: [],
   show: false,
   open() {
     this.show = true
   },
   close() {
     this.show = false
   },
   select(optionIndex) {
       if (!this.options[optionIndex].selected) {
         this.options[optionIndex].selected = true;
         this.selected.push(optionIndex);
       } else {
         this.remove(optionIndex);
       }
   },
   remove(optionIndex) {
     this.selected.splice(this.selected.lastIndexOf(optionIndex), 1);
     this.options[optionIndex].selected = false;
   }
 }
}